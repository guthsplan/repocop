"""
Rule-based execution plan builder.
No LLM. Emits a structured plan and a verdict from a fixed taxonomy.
"""
from __future__ import annotations

# ---- Verdict taxonomy -------------------------------------------------------
VERDICT = {
    # Ready
    "READY_TO_RUN":                  "READY_TO_RUN",
    # Blocked — hard stops
    "BLOCKED_REPO_PAPER_MISMATCH":   "BLOCKED_REPO_PAPER_MISMATCH",
    "BLOCKED_NO_EVAL_SCRIPT":        "BLOCKED_NO_EVAL_SCRIPT",
    "BLOCKED_DEMO_ONLY":             "BLOCKED_DEMO_ONLY",
    "BLOCKED_NO_METRIC_SCRIPT":      "BLOCKED_NO_METRIC_SCRIPT",
    "BLOCKED_MISSING_CHECKPOINT":    "BLOCKED_MISSING_CHECKPOINT",
    "BLOCKED_MISSING_DATASET":       "BLOCKED_MISSING_DATASET",
    "BLOCKED_ENVIRONMENT":           "BLOCKED_ENVIRONMENT",
    # Suspicious — run may produce misleading results
    "SUSPICIOUS_PRECOMPUTED_RESULTS": "SUSPICIOUS_PRECOMPUTED_RESULTS",
    "SUSPICIOUS_HARDCODED_VALUES":    "SUSPICIOUS_HARDCODED_VALUES",
    "SUSPICIOUS_SUBSET_EVAL":         "SUSPICIOUS_SUBSET_EVAL",
    "SUSPICIOUS_CONFIG_MISMATCH":     "SUSPICIOUS_CONFIG_MISMATCH",
    # Partial
    "PARTIAL_EVAL_NO_METRIC_EXTRACTION": "PARTIAL_EVAL_NO_METRIC_EXTRACTION",
    # Fallback
    "BLOCKED": "BLOCKED",
    "INCONCLUSIVE": "INCONCLUSIVE",
}


def _contains(data: object, *keywords: str) -> bool:
    text = str(data).lower()
    return any(k.lower() in text for k in keywords)


def build_execution_plan(
    config: dict,
    env: dict,
    repo_scan: dict,
    eval_targets: dict,
    repo_match: dict,
    code_completeness: dict | None = None,
) -> dict:
    blockers: list[dict] = []
    warnings: list[dict] = []

    # ------------------------------------------------------------------ #
    # 1. Repo-paper mismatch (highest priority — stop before anything)
    # ------------------------------------------------------------------ #
    identity = repo_match.get("repo_identity", {})
    if identity.get("possible_mismatch_with_paper"):
        blockers.append({
            "type": "possible_repo_paper_mismatch",
            "message": identity.get("reason") or
                       "Repository domain does not appear to match the paper.",
        })

    # ------------------------------------------------------------------ #
    # 2. No eval script at all
    # ------------------------------------------------------------------ #
    has_eval = bool(repo_scan.get("candidate_eval_files"))
    has_demo = bool(repo_scan.get("candidate_demo_files"))

    if not has_eval:
        if has_demo:
            blockers.append({
                "type": "demo_only",
                "message": "Repository has demo/inference scripts but no benchmark evaluation "
                           "script. A demo is not a reproducibility harness.",
            })
        else:
            blockers.append({
                "type": "no_eval_script",
                "message": "No candidate evaluation script found in repository.",
            })

    # ------------------------------------------------------------------ #
    # 3. All repo-match targets blocked
    # ------------------------------------------------------------------ #
    target_matches = repo_match.get("target_matches", [])
    if target_matches and all(m.get("status") == "blocked" for m in target_matches):
        if not any(b["type"] in {"demo_only", "no_eval_script"} for b in blockers):
            blockers.append({
                "type": "all_targets_blocked",
                "message": "All eval targets were assessed as blocked in repo match.",
            })

    # ------------------------------------------------------------------ #
    # 4. Missing required artifacts
    # ------------------------------------------------------------------ #
    resources = config.get("resources", {})
    needs_ckpt = _contains(eval_targets, "checkpoint", "ckpt", "pretrained", "weights")
    needs_data = _contains(eval_targets, "dataset", "benchmark", "split", "test set")

    if needs_ckpt and not resources.get("checkpoint_path"):
        blockers.append({
            "type": "missing_checkpoint",
            "message": "Eval target requires a checkpoint. Provide --checkpoint-path.",
        })
    if needs_data and not resources.get("dataset_path"):
        blockers.append({
            "type": "missing_dataset",
            "message": "Eval target requires a dataset. Provide --dataset-path.",
        })

    # ------------------------------------------------------------------ #
    # 5. Suspicious indicators (non-blocking warnings)
    # ------------------------------------------------------------------ #
    if code_completeness:
        if code_completeness.get("precomputed_warning_files"):
            warnings.append({
                "type": "suspicious_precomputed_results",
                "message": "Possible precomputed result files found: "
                           + str(code_completeness["precomputed_warning_files"][:3]),
            })
        if code_completeness.get("checks", {}).get("metric_script") == "missing" and has_eval:
            warnings.append({
                "type": "no_metric_script",
                "message": "Eval script found but no metric computation code detected. "
                           "Running eval may not produce paper-comparable numbers.",
            })

    if repo_scan.get("bundled_checkpoints"):
        warnings.append({
            "type": "bundled_checkpoint",
            "message": "Checkpoint files are committed inside the repo — "
                       "may be demo weights, not full paper weights.",
        })

    # ------------------------------------------------------------------ #
    # 6. Emit plan
    # ------------------------------------------------------------------ #
    if blockers:
        return {
            "status": "blocked",
            "verdict": _classify_blockers(blockers),
            "blockers": blockers,
            "warnings": warnings,
            "setup_plan": [],
            "eval_plan": [],
            "user_actions_required": _user_actions(blockers),
        }

    # If we reach here: no hard blockers
    setup = _build_setup(repo_scan)
    eval_cmds = _build_eval_commands(repo_match)

    # Downgrade to PARTIAL if metric extraction looks impossible
    if warnings and any(w["type"] == "no_metric_script" for w in warnings):
        verdict = VERDICT["PARTIAL_EVAL_NO_METRIC_EXTRACTION"]
    else:
        verdict = VERDICT["READY_TO_RUN"]

    return {
        "status": "ready" if verdict == VERDICT["READY_TO_RUN"] else "partial",
        "verdict": verdict,
        "blockers": [],
        "warnings": warnings,
        "setup_plan": setup,
        "eval_plan": eval_cmds,
        "user_actions_required": [],
    }


def _classify_blockers(blockers: list[dict]) -> str:
    types = {b["type"] for b in blockers}
    if "possible_repo_paper_mismatch" in types:
        return VERDICT["BLOCKED_REPO_PAPER_MISMATCH"]
    if "demo_only" in types:
        return VERDICT["BLOCKED_DEMO_ONLY"]
    if "no_eval_script" in types or "all_targets_blocked" in types:
        return VERDICT["BLOCKED_NO_EVAL_SCRIPT"]
    if "missing_checkpoint" in types and "missing_dataset" not in types:
        return VERDICT["BLOCKED_MISSING_CHECKPOINT"]
    if "missing_dataset" in types and "missing_checkpoint" not in types:
        return VERDICT["BLOCKED_MISSING_DATASET"]
    if "missing_checkpoint" in types and "missing_dataset" in types:
        return VERDICT["BLOCKED_MISSING_CHECKPOINT"]
    return VERDICT["BLOCKED"]


def _user_actions(blockers: list[dict]) -> list[str]:
    actions: list[str] = []
    types = {b["type"] for b in blockers}
    if "possible_repo_paper_mismatch" in types:
        actions.append("Provide the official repository that matches the paper.")
    if "demo_only" in types:
        actions.append("Provide the benchmark evaluation script if it exists separately.")
    if "no_eval_script" in types or "all_targets_blocked" in types:
        actions.append("Provide an evaluation script that computes the reported metrics.")
    if "missing_checkpoint" in types:
        actions.append("Provide a model checkpoint with --checkpoint-path.")
    if "missing_dataset" in types:
        actions.append("Provide the dataset path with --dataset-path.")
    return actions


def _build_setup(repo_scan: dict) -> list[str]:
    cmds: list[str] = []
    if repo_scan.get("has_environment_yml"):
        cmds.append("conda env create -f environment.yml")
    elif repo_scan.get("has_requirements"):
        cmds.append("conda create -y -n audit_env python=3.10")
        cmds.append("conda run -n audit_env pip install -r requirements.txt")
    elif repo_scan.get("has_setup_py"):
        cmds.append("pip install -e .")
    elif repo_scan.get("has_pyproject"):
        cmds.append("pip install -e .")
    return cmds


def _build_eval_commands(repo_match: dict) -> list[str]:
    return [
        m["candidate_command"]
        for m in repo_match.get("target_matches", [])
        if m.get("status") == "supported" and m.get("candidate_command")
    ]
