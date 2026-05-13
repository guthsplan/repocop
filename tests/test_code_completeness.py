from pathlib import Path
from research_auditor.probes.code_completeness import score_completeness


def _make_repo(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return tmp_path


def _scan(tmp_path: Path) -> dict:
    from research_auditor.probes.repo_scan import scan_repo
    return scan_repo(tmp_path)


def test_full_repo_scores_high(tmp_path):
    repo = _make_repo(tmp_path, {
        "requirements.txt": "torch\n",
        "README.md": "Download checkpoint: https://huggingface.co/org/model\n"
                     "Download dataset with: wget http://example.com/data.zip\n"
                     "GPU: A100\n",
        "eval.py": "from sklearn.metrics import accuracy_score\ndef evaluate(): pass\n",
        "train.py": "# training\n",
        "configs/eval.yaml": "seed: 42\n",
        "demo.py": "# demo\n",
    })
    result = score_completeness(repo, _scan(repo))
    assert result["score"] >= 75
    assert result["level"] == "high"
    assert result["checks"]["eval_script"] == "found"
    assert result["checks"]["dependency_file"] == "found"
    assert result["checks"]["pretrained_checkpoint_link"] == "found"


def test_empty_repo_scores_zero(tmp_path):
    repo = _make_repo(tmp_path, {"src/model.py": "pass\n"})
    result = score_completeness(repo, _scan(repo))
    assert result["score"] == 0
    assert result["level"] == "low"


def test_demo_only_noted(tmp_path):
    repo = _make_repo(tmp_path, {
        "requirements.txt": "torch\n",
        "inference.py": "# demo\n",
    })
    result = score_completeness(repo, _scan(repo))
    notes_text = " ".join(result["notes"])
    assert "demo" in notes_text.lower() or "inference" in notes_text.lower()
    assert result["checks"]["eval_script"] == "missing"


def test_precomputed_warning(tmp_path):
    repo = _make_repo(tmp_path, {"results.py": "pass"})
    (tmp_path / "predictions.pkl").write_bytes(b"\x80\x04\x95")

    result = score_completeness(repo, _scan(repo))
    assert len(result["precomputed_warning_files"]) > 0
