import pytest
from pathlib import Path
from research_auditor.core.safety import validate_command, ensure_inside_workdir


def test_sudo_blocked_by_default():
    with pytest.raises(ValueError, match="sudo"):
        validate_command("sudo apt-get install vim", allow_sudo=False)


def test_sudo_allowed_when_flag_set():
    validate_command("sudo apt-get install vim", allow_sudo=True)


def test_forbidden_patterns():
    with pytest.raises(ValueError):
        validate_command("rm -rf /home", allow_sudo=False)


def test_safe_command():
    validate_command("python eval.py --config configs/eval.yaml")


def test_ensure_inside_workdir_ok(tmp_path):
    sub = tmp_path / "runs" / "audit"
    sub.mkdir(parents=True)
    ensure_inside_workdir(sub, tmp_path)


def test_ensure_inside_workdir_escape(tmp_path):
    outside = tmp_path.parent / "other"
    outside.mkdir(exist_ok=True)
    with pytest.raises(ValueError, match="escapes workdir"):
        ensure_inside_workdir(outside, tmp_path)
