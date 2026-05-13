from pathlib import Path
from datetime import datetime
from ..core.run_dir import load_yaml, load_json


def write_summary(run_dir: Path) -> str:
    cfg          = load_yaml(run_dir / "00_input.yaml") or {}
    env          = load_json(run_dir / "01_env_probe.json") or {}
    repo_scan    = load_json(run_dir / "02_repo_scan.json") or {}
    completeness = load_json(run_dir / "02b_code_completeness.json") or {}
    eval_targets = load_yaml(run_dir / "03_paper_eval_targets.yaml") or {}
    domain_info  = load_yaml(run_dir / "03b_domain.yaml") or {}
    repo_match   = load_yaml(run_dir / "04_repo_match.yaml") or {}
    plan         = load_yaml(run_dir / "05_execution_plan.yaml") or {}
    provenance   = load_json(run_dir / "07_provenance.json") or {}

    L: list[str] = []

    def ln(s: str = "") -> None:
        L.append(s)

    def section(title: str) -> None:
        ln()
        ln(title)
        ln("-" * 40)

    ln("Audit Summary")
    ln("=" * 50)
    ln(f"Date      : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    ln(f"Run dir   : {run_dir}")
    if provenance.get("duration_s"):
        ln(f"Duration  : {provenance['duration_s']}s")

    section("Input")
    paper_url = cfg.get("paper", {}).get("url") or ""
    repo_url  = cfg.get("repo", {}).get("url") or ""
    ln(f"  Paper : {paper_url or '(none)'}")
    ln(f"  Repo  : {repo_url or '(none)'}")
    if provenance.get("repo_commit"):
        ln(f"  Commit: {provenance['repo_commit'][:12]}")

    section("Verdict")
    verdict = plan.get("verdict", "UNKNOWN")
    status  = plan.get("status", "unknown")
    ln(f"  {verdict}  [{status}]")

    blockers = plan.get("blockers", [])
    if blockers:
        ln()
        ln("  Blockers:")
        for b in blockers:
            ln(f"    [{b.get('type','?')}] {b.get('message','')}")

    warnings = plan.get("warnings", [])
    if warnings:
        ln()
        ln("  Warnings:")
        for w in warnings:
            ln(f"    [{w.get('type','?')}] {w.get('message','')}")

    actions = plan.get("user_actions_required", [])
    if actions:
        ln()
        ln("  User actions required:")
        for a in actions:
            ln(f"    - {a}")

    section("Environment")
    ln(f"  Python : {env.get('python', '?')}")
    ln(f"  GPU    : {env.get('gpu', '?')}")
    ln(f"  CUDA   : {env.get('cuda', '?')}")
    ln(f"  sudo   : {env.get('sudo_allowed', False)}")

    section("Domain")
    domain_id = domain_info.get("inferred_domain_id", "unknown")
    ln(f"  Inferred : {domain_id}")
    ln(f"  Template : {'loaded' if domain_info.get('template_found') else 'not found'}")

    section("Code Completeness")
    if completeness.get("score") is not None:
        score = completeness["score"]
        level = completeness.get("level", "?")
        ln(f"  Score  : {score}/100  ({level})")
        checks = completeness.get("checks", {})
        for k, v in checks.items():
            if isinstance(v, bool):
                sym = "yes" if v else "no"
            else:
                sym = str(v)
            ln(f"    {k:<32}: {sym}")
        notes = completeness.get("notes", [])
        if notes:
            ln()
            ln("  Notes:")
            for n in notes:
                ln(f"    - {n}")
    else:
        ln("  (not computed)")

    section("Extracted Eval Targets")
    targets = eval_targets.get("eval_targets", [])
    if targets:
        for t in targets:
            ln(f"  {t.get('id','?')} [{t.get('priority','?')}] {t.get('claim','')[:70]}")
            ln(f"      metric={t.get('metric','?')}  dataset={t.get('dataset','?')}  "
               f"value={t.get('reported_value','?')}")
    elif eval_targets.get("status") == "parse_failed":
        ln("  [LLM parse failed — see raw_llm/03_eval_targets_raw.md]")
    else:
        ln("  (none extracted)")

    section("Repository Scan")
    ln(f"  Files total       : {repo_scan.get('num_files', '?')}")
    ln(f"  requirements.txt  : {repo_scan.get('has_requirements', '?')}")
    ln(f"  environment.yml   : {repo_scan.get('has_environment_yml', '?')}")
    ln(f"  Dockerfile        : {repo_scan.get('has_dockerfile', '?')}")
    ln(f"  eval candidates   : {len(repo_scan.get('candidate_eval_files', []))}")
    ln(f"  demo candidates   : {len(repo_scan.get('candidate_demo_files', []))}")
    pre = repo_scan.get("precomputed_warning_files", [])
    if pre:
        ln(f"  precomputed files : {pre[:3]}")

    discrepancies = repo_match.get("discrepancies", [])
    if discrepancies:
        section("Discrepancies")
        for d in discrepancies:
            sev  = d.get("severity", "?") if isinstance(d, dict) else "?"
            text = d.get("text", str(d))   if isinstance(d, dict) else str(d)
            ln(f"  [{sev}] {text}")

    section("Execution Plan")
    setup = plan.get("setup_plan", [])
    eval_cmds = plan.get("eval_plan", [])
    if setup:
        ln("  Setup commands:")
        for c in setup:
            ln(f"    $ {c}")
    if eval_cmds:
        ln("  Eval commands:")
        for c in eval_cmds:
            ln(f"    $ {c}")
    if not setup and not eval_cmds:
        ln("  (none — plan is blocked)")

    section("Artifacts")
    for p in sorted(run_dir.rglob("*")):
        if p.is_file():
            ln(f"  {p.relative_to(run_dir)}")

    return "\n".join(L)
