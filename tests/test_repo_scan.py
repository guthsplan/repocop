from pathlib import Path
from research_auditor.probes.repo_scan import scan_repo


def test_scan_minimal_repo(tmp_path):
    (tmp_path / "requirements.txt").write_text("torch\n")
    (tmp_path / "eval.py").write_text("# eval\n")
    (tmp_path / "README.md").write_text("# Test\n")

    result = scan_repo(tmp_path)

    assert result["has_requirements"] is True
    assert result["has_dockerfile"] is False
    assert "eval.py" in result["candidate_eval_files"]
    assert result["num_files"] == 3


def test_scan_ignores_git_dir(tmp_path):
    git_dir = tmp_path / ".git" / "objects"
    git_dir.mkdir(parents=True)
    (git_dir / "packed-refs").write_text("ref\n")
    (tmp_path / "eval.py").write_text("pass\n")

    result = scan_repo(tmp_path)
    assert result["num_files"] == 1


def test_scan_environment_yml(tmp_path):
    (tmp_path / "environment.yml").write_text("name: myenv\n")
    result = scan_repo(tmp_path)
    assert result["has_environment_yml"] is True
