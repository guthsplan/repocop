"""
Rule-based completeness checker — no LLM.
Takes repo_path + repo_scan dict, returns a scored checklist.
"""
from __future__ import annotations
import re
from pathlib import Path

_CHECKPOINT_PATTERNS = [
    r"\.pth\b", r"\.ckpt\b", r"\.safetensors\b",
    r"huggingface\.co", r"drive\.google\.com",
    r"zenodo\.org", r"dropbox\.com", r"download\.pytorch\.org",
    r"pretrained", r"model_weights",
]
_METRIC_PATTERNS = [
    r"\bpsnr\b", r"\bssim\b", r"\blpips\b",
    r"\bmap\b", r"\bap@\b", r"\bap50\b", r"\bf1_score\b",
    r"\bbleu\b", r"\brouge\b", r"\bexact_match\b",
    r"compute_metric", r"calculate_\w+score", r"sklearn\.metrics",
    r"evaluate\(", r"metric\.update",
]
_DATASET_PATTERNS = [
    r"\bdownload\b", r"\bwget\b", r"\bgdown\b",
    r"data_root\s*=", r"dataset_path\s*=", r"--data\b",
    r"\bunzip\b", r"\bpreprocess\b",
]
_SEED_PATTERNS = [r"seed\s*=\s*\d", r"set_seed\(", r"manual_seed\(", r"random_state\s*="]
_HARDWARE_PATTERNS = [r"\bGPU\b", r"\bCUDA\b", r"\bA100\b", r"\bV100\b", r"\bRTX\b", r"\bTPU\b"]
_PRECOMPUTED_NAMES = ["predictions", "cached_", "precomputed", "result.json", "results.pkl"]
_PRECOMPUTED_EXTS = {".pkl", ".json", ".csv", ".npy", ".npz"}


def _readme_text(repo_path: Path) -> str:
    for name in ["README.md", "README.rst", "README.txt", "readme.md"]:
        p = repo_path / name
        if p.exists():
            return p.read_text(encoding="utf-8", errors="ignore")
    return ""


def _any_match(patterns: list[str], texts: list[str]) -> bool:
    rx = re.compile("|".join(patterns), re.IGNORECASE)
    return any(rx.search(t) for t in texts)


def _scan_py_files(repo_path: Path, file_list: list[str], patterns: list[str]) -> bool:
    rx = re.compile("|".join(patterns), re.IGNORECASE)
    for rel in file_list[:40]:
        p = repo_path / rel
        if not p.exists():
            continue
        try:
            if rx.search(p.read_text(encoding="utf-8", errors="ignore")):
                return True
        except OSError:
            continue
    return False


def _find_precomputed(all_files: list[str]) -> list[str]:
    found = []
    for f in all_files:
        stem = Path(f).stem.lower()
        ext = Path(f).suffix.lower()
        if ext in _PRECOMPUTED_EXTS and any(p in stem for p in _PRECOMPUTED_NAMES):
            found.append(f)
    return found[:20]


def score_completeness(repo_path: Path, repo_scan: dict) -> dict:
    all_files: list[str] = []
    for p in repo_path.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.relative_to(repo_path))
        if rel.startswith(".git/"):
            continue
        all_files.append(rel)

    readme = _readme_text(repo_path)
    py_files = [f for f in all_files if f.endswith(".py")]

    dep_found = any([
        repo_scan.get("has_requirements"),
        repo_scan.get("has_environment_yml"),
        repo_scan.get("has_setup_py"),
        repo_scan.get("has_pyproject"),
    ])
    eval_found = bool(repo_scan.get("candidate_eval_files"))
    train_found = bool(repo_scan.get("candidate_train_files"))
    demo_found = bool(repo_scan.get("candidate_demo_files"))
    config_found = bool(repo_scan.get("candidate_config_files"))

    ckpt_found = _any_match(_CHECKPOINT_PATTERNS, [readme]) or \
                 _scan_py_files(repo_path, py_files[:15], _CHECKPOINT_PATTERNS)
    dataset_found = _any_match(_DATASET_PATTERNS, [readme]) or \
                    _scan_py_files(repo_path, py_files[:15], _DATASET_PATTERNS)
    metric_found = _scan_py_files(repo_path, py_files, _METRIC_PATTERNS)

    result_files = [f for f in all_files if Path(f).name in
                    {"results.json", "results.txt", "results.csv", "eval_results.json"}]
    results_found = bool(result_files)

    seed_mentioned = _any_match(_SEED_PATTERNS, [readme] + [
        (repo_path / f).read_text("utf-8", errors="ignore")
        for f in py_files[:5] if (repo_path / f).exists()
    ])
    hw_mentioned = _any_match(_HARDWARE_PATTERNS, [readme])
    precomputed = _find_precomputed(all_files)

    score = sum([
        15 if dep_found else 0,
        20 if eval_found else 0,
        15 if ckpt_found else 0,
        15 if dataset_found else 0,
        10 if config_found else 0,
        15 if metric_found else 0,
        5  if train_found else 0,
        5  if results_found else 0,
    ])
    level = "high" if score >= 75 else ("medium" if score >= 50 else "low")

    notes: list[str] = []
    if not eval_found and demo_found:
        notes.append("Has demo/inference script but no benchmark eval script.")
    if not ckpt_found:
        notes.append("No checkpoint download link or weight file reference found.")
    if not dataset_found:
        notes.append("No dataset download or preprocessing instruction found.")
    if precomputed:
        notes.append(f"Possible precomputed result files detected: {precomputed[:3]}")
    if not metric_found:
        notes.append("No metric computation code found in Python files.")

    return {
        "checks": {
            "dependency_file":            "found" if dep_found else "missing",
            "eval_script":                "found" if eval_found else "missing",
            "training_script":            "found" if train_found else "missing",
            "demo_script":                "found" if demo_found else "missing",
            "pretrained_checkpoint_link": "found" if ckpt_found else "missing",
            "dataset_instruction":        "found" if dataset_found else "missing",
            "config_file":                "found" if config_found else "missing",
            "metric_script":              "found" if metric_found else "missing",
            "result_files":               "found" if results_found else "missing",
            "random_seed_mentioned":      seed_mentioned,
            "hardware_mentioned":         hw_mentioned,
        },
        "precomputed_warning_files": precomputed,
        "score": score,
        "level": level,
        "notes": notes,
    }
