from __future__ import annotations
import time
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from .schemas.models import AuditConfig
from .core.run_dir import create_run_dir, save_yaml, save_json, save_text
from .probes.env_probe import probe_environment
from .probes.repo_scan import scan_repo
from .probes.code_completeness import score_completeness
from .repo.clone import prepare_repo
from .paper.fetch import fetch_paper_text
from .paper.eval_target_agent import extract_eval_targets
from .repo.repo_match_agent import match_repo_to_eval_targets
from .domain.template_loader import get_domain_context
from .planning.execution_plan import build_execution_plan
from .execution.local_executor import LocalExecutor
from .reporting.summary import write_summary

console = Console()


def _step(label: str) -> None:
    console.print(f"  [cyan]>[/cyan] {label}")


def run_audit(config: AuditConfig) -> Path:
    start_ts = datetime.now(timezone.utc)
    start_time = time.time()

    run_name = config.run_name or (
        config.paper.url.replace("https://", "").replace("http://", "").split("/")[0]
        if config.paper.url else "audit"
    )
    run_dir = create_run_dir(config.execution.workdir, run_name)
    console.print(f"\n[bold]Run directory:[/bold] {run_dir}\n")

    save_yaml(run_dir / "00_input.yaml", config.model_dump())

    # 01 — Environment probe
    _step("Probing environment")
    env = probe_environment(
        allow_sudo=config.safety.allow_sudo,
        log_path=run_dir / "logs" / "env_probe.log",
    )
    save_json(run_dir / "01_env_probe.json", env)

    # 02 — Clone / locate repo
    _step("Cloning / locating repository")
    repo_path: Path | None = None
    try:
        repo_path = prepare_repo(
            repo_url=config.repo.url,
            repo_local=config.repo.local_path,
            run_dir=run_dir,
            log_path=run_dir / "logs" / "clone.log",
        )
    except Exception as e:
        _save_step_failure(run_dir, "clone", str(e))

    repo_scan: dict = {}
    if repo_path:
        _step("Scanning repository structure")
        repo_scan = scan_repo(repo_path)
        save_json(run_dir / "02_repo_scan.json", repo_scan)
    else:
        save_json(run_dir / "02_repo_scan.json", {"status": "failed", "reason": "clone failed"})

    # 02b — Code completeness (rule-based, no LLM)
    completeness: dict = {}
    if repo_path:
        _step("Checking code completeness")
        try:
            completeness = score_completeness(repo_path, repo_scan)
        except Exception as e:
            completeness = {"status": "failed", "error": str(e)}
        save_json(run_dir / "02b_code_completeness.json", completeness)

    # 03 — Paper eval target extraction (LLM call 1/2)
    _step("Fetching paper text")
    try:
        paper_text = fetch_paper_text(
            paper_url=config.paper.url,
            pdf_path=config.paper.pdf_path,
            run_dir=run_dir,
        )
    except Exception as e:
        paper_text = f"[paper fetch failed: {e}]"
        console.print(f"    [yellow]warning:[/yellow] {e}")

    _step("Extracting eval targets from paper  (LLM 1/2)")
    eval_targets = extract_eval_targets(paper_text, run_dir)
    save_yaml(run_dir / "03_paper_eval_targets.yaml", eval_targets)

    # Domain template inference
    domain_id, domain_ctx = get_domain_context(eval_targets)
    save_yaml(run_dir / "03b_domain.yaml", {
        "inferred_domain_id": domain_id,
        "template_found": bool(domain_ctx),
    })

    # 04 — Repo match (LLM call 2/2)
    repo_match: dict = {"status": "skipped", "reason": "no repo available"}
    if repo_path:
        _step(f"Matching repo to eval targets  (LLM 2/2)  [domain: {domain_id}]")
        repo_match = match_repo_to_eval_targets(
            repo_path=repo_path,
            repo_scan=repo_scan,
            eval_targets=eval_targets,
            run_dir=run_dir,
            domain_context=domain_ctx,
        )
    save_yaml(run_dir / "04_repo_match.yaml", repo_match)

    # 05 — Execution plan (rule-based)
    _step("Building execution plan")
    plan = build_execution_plan(
        config=config.model_dump(),
        env=env,
        repo_scan=repo_scan,
        eval_targets=eval_targets,
        repo_match=repo_match,
        code_completeness=completeness or None,
    )
    save_yaml(run_dir / "05_execution_plan.yaml", plan)

    # 06 — Execute (only if explicitly requested and plan is ready/partial)
    result: dict = {"status": "skipped", "reason": "execute=false"}
    if config.execution.execute and plan["status"] in {"ready", "partial"}:
        _step("Executing plan")
        result = _run_plan(plan, repo_path, config)
    save_json(run_dir / "06_run_result.json", result)

    # 07 — Provenance (always generated last)
    end_ts = datetime.now(timezone.utc)
    provenance = _build_provenance(
        run_dir=run_dir,
        config=config,
        env=env,
        repo_path=repo_path,
        plan=plan,
        result=result,
        start_ts=start_ts,
        end_ts=end_ts,
        duration_s=round(time.time() - start_time, 1),
    )
    save_json(run_dir / "07_provenance.json", provenance)

    # Summary
    _step("Writing audit summary")
    summary = write_summary(run_dir)
    save_text(run_dir / "audit_summary.txt", summary)

    verdict = plan.get("verdict", "UNKNOWN")
    color = "green" if "READY" in verdict else ("yellow" if "SUSPICIOUS" in verdict else "red")
    console.print(f"\n[bold {color}]Verdict: {verdict}[/bold {color}]")
    console.print(f"Summary  → {run_dir / 'audit_summary.txt'}\n")

    return run_dir


def _save_step_failure(run_dir: Path, step: str, reason: str) -> None:
    console.print(f"    [red]failed:[/red] {step}: {reason}")
    (run_dir / f"STEP_FAILED_{step.upper()}.txt").write_text(reason, encoding="utf-8")


def _run_plan(plan: dict, repo_path: Path | None, config: AuditConfig) -> dict:
    executor = LocalExecutor(allow_sudo=config.safety.allow_sudo)
    log = Path(config.execution.workdir).expanduser() / "execution.log"
    results: list[dict] = []

    for cmd in plan.get("setup_plan", []):
        out = executor.run(cmd, cwd=repo_path, log_path=log, timeout=300)
        results.append(out.to_dict())
        if not out.success:
            return {"status": "setup_failed", "results": results, "failed_command": cmd}

    for cmd in plan.get("eval_plan", []):
        out = executor.run(cmd, cwd=repo_path, log_path=log, timeout=600)
        results.append(out.to_dict())

    return {"status": "completed", "results": results}


def _get_repo_commit(repo_path: Path | None) -> str | None:
    if not repo_path:
        return None
    from .core.shell import run_command
    out = run_command(f"git -C {repo_path} rev-parse HEAD", timeout=10)
    return out["stdout"] if out["success"] else None


def _build_provenance(
    run_dir: Path,
    config: AuditConfig,
    env: dict,
    repo_path: Path | None,
    plan: dict,
    result: dict,
    start_ts: datetime,
    end_ts: datetime,
    duration_s: float,
) -> dict:
    created_files = [
        str(p.relative_to(run_dir))
        for p in sorted(run_dir.rglob("*"))
        if p.is_file()
    ]
    executed_cmds = (
        plan.get("setup_plan", []) + plan.get("eval_plan", [])
        if result.get("status") == "completed" else []
    )
    return {
        "run_dir": str(run_dir),
        "start_time": start_ts.isoformat(),
        "end_time": end_ts.isoformat(),
        "duration_s": duration_s,
        "paper_url": config.paper.url,
        "repo_url": config.repo.url,
        "repo_commit": _get_repo_commit(repo_path),
        "python": env.get("python", ""),
        "cuda": env.get("cuda", ""),
        "gpu": env.get("gpu", ""),
        "sudo_allowed": config.safety.allow_sudo,
        "executed_commands": executed_cmds,
        "created_files": created_files,
    }
