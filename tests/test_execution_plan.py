from research_auditor.planning.execution_plan import build_execution_plan

BASE_CONFIG = {
    "resources": {"checkpoint_path": None, "dataset_path": None},
    "safety": {"allow_sudo": False},
}

EVAL_TARGETS_WITH_CHECKPOINT = {
    "eval_targets": [{"id": "E1", "claim": "...", "metric": "mAP", "dataset": "VOC", "required_artifacts": ["checkpoint"]}]
}

EVAL_TARGETS_SIMPLE = {
    "eval_targets": [{"id": "E1", "claim": "...", "metric": "BLEU", "dataset": "WMT"}]
}


def test_blocked_when_no_eval_script():
    plan = build_execution_plan(
        config=BASE_CONFIG,
        env={},
        repo_scan={"candidate_eval_files": [], "has_requirements": True},
        eval_targets=EVAL_TARGETS_SIMPLE,
        repo_match={"repo_identity": {}, "target_matches": []},
    )
    assert plan["status"] == "blocked"
    assert "BLOCKED" in plan["verdict"]


def test_blocked_when_checkpoint_missing():
    plan = build_execution_plan(
        config=BASE_CONFIG,
        env={},
        repo_scan={"candidate_eval_files": ["eval.py"]},
        eval_targets=EVAL_TARGETS_WITH_CHECKPOINT,
        repo_match={
            "repo_identity": {},
            "target_matches": [{"target_id": "E1", "status": "supported", "candidate_command": "python eval.py"}],
        },
    )
    assert plan["status"] == "blocked"
    assert plan["verdict"] == "BLOCKED_MISSING_CHECKPOINT"


def test_blocked_on_mismatch():
    plan = build_execution_plan(
        config=BASE_CONFIG,
        env={},
        repo_scan={"candidate_eval_files": ["eval.py"]},
        eval_targets=EVAL_TARGETS_SIMPLE,
        repo_match={
            "repo_identity": {
                "possible_mismatch_with_paper": True,
                "reason": "Repo appears to be a different project.",
            },
            "target_matches": [],
        },
    )
    assert plan["verdict"] == "BLOCKED_REPO_PAPER_MISMATCH"
