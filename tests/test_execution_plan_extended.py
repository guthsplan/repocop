from research_auditor.planning.execution_plan import build_execution_plan

BASE_CONFIG = {"resources": {"checkpoint_path": None, "dataset_path": None}}


def _plan(**kwargs):
    defaults = dict(
        config=BASE_CONFIG,
        env={},
        repo_scan={"candidate_eval_files": [], "candidate_demo_files": [], "has_requirements": False},
        eval_targets={},
        repo_match={"repo_identity": {}, "target_matches": [], "discrepancies": []},
        code_completeness=None,
    )
    defaults.update(kwargs)
    return build_execution_plan(**defaults)


def test_blocked_demo_only():
    p = _plan(
        repo_scan={
            "candidate_eval_files": [],
            "candidate_demo_files": ["demo.py"],
            "has_requirements": True,
        }
    )
    assert p["verdict"] == "BLOCKED_DEMO_ONLY"
    assert any(b["type"] == "demo_only" for b in p["blockers"])


def test_blocked_no_eval():
    p = _plan()
    assert "BLOCKED" in p["verdict"]
    assert p["status"] == "blocked"


def test_suspicious_precomputed():
    p = _plan(
        repo_scan={"candidate_eval_files": ["eval.py"], "candidate_demo_files": [], "bundled_checkpoints": []},
        repo_match={"repo_identity": {}, "target_matches": [{"target_id": "E1", "status": "supported", "candidate_command": "python eval.py"}]},
        code_completeness={"precomputed_warning_files": ["predictions.pkl"], "checks": {"metric_script": "found"}, "score": 60, "level": "medium", "notes": []},
    )
    # Should have a warning but not a hard blocker
    assert any(w["type"] == "suspicious_precomputed_results" for w in p.get("warnings", []))


def test_partial_no_metric_script():
    p = _plan(
        repo_scan={"candidate_eval_files": ["eval.py"], "candidate_demo_files": [], "bundled_checkpoints": [], "has_requirements": True},
        repo_match={"repo_identity": {}, "target_matches": [{"target_id": "E1", "status": "supported", "candidate_command": "python eval.py"}]},
        code_completeness={"precomputed_warning_files": [], "checks": {"metric_script": "missing"}, "score": 40, "level": "low", "notes": []},
    )
    assert p["verdict"] == "PARTIAL_EVAL_NO_METRIC_EXTRACTION"
    assert p["status"] == "partial"


def test_warnings_from_bundled_checkpoint():
    p = _plan(
        repo_scan={
            "candidate_eval_files": ["eval.py"],
            "candidate_demo_files": [],
            "bundled_checkpoints": ["weights/model.pth"],
            "has_requirements": True,
        },
        repo_match={
            "repo_identity": {},
            "target_matches": [{"target_id": "E1", "status": "supported", "candidate_command": "python eval.py"}],
        },
        code_completeness={"precomputed_warning_files": [], "checks": {"metric_script": "found"}, "score": 75, "level": "high", "notes": []},
    )
    assert any(w["type"] == "bundled_checkpoint" for w in p.get("warnings", []))
