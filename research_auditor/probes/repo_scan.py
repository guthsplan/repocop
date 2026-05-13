from pathlib import Path

EVAL_KEYWORDS = ["eval", "evaluate", "benchmark", "score", "metric", "test"]
DEMO_KEYWORDS = ["demo", "infer", "inference", "predict", "sample"]
TRAIN_KEYWORDS = ["train", "finetune", "pretrain"]
CONFIG_KEYWORDS = ["config", "cfg"]
CHECKPOINT_EXTS = {".pth", ".pt", ".ckpt", ".safetensors", ".bin"}
PRECOMPUTED_NAMES = ["predictions", "cached_", "precomputed", "cached_results"]
PRECOMPUTED_EXTS = {".pkl", ".npy", ".npz"}

MAX_FILE_SIZE = 2_000_000  # 2MB
MAX_CANDIDATES = 50


def _find_by_keywords(files: list[str], keywords: list[str]) -> list[str]:
    out = []
    for f in files:
        lower = f.lower()
        name = Path(f).stem.lower()
        if any(w in name for w in keywords):
            out.append(f)
    return out[:MAX_CANDIDATES]


def scan_repo(repo_path: Path) -> dict:
    all_files = []
    for p in repo_path.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.relative_to(repo_path))
        if rel.startswith(".git/"):
            continue
        try:
            if p.stat().st_size > MAX_FILE_SIZE:
                continue
        except OSError:
            continue
        all_files.append(rel)

    all_files_lower = [f.lower() for f in all_files]

    readme_files = [f for f in all_files if Path(f).name.lower().startswith("readme")]
    top_level = [f for f in all_files if "/" not in f]

    python_files = [f for f in all_files if f.endswith(".py")]
    yaml_files = [f for f in all_files if f.endswith((".yaml", ".yml"))]
    shell_files = [f for f in all_files if f.endswith(".sh")]

    has_requirements = any("requirements" in f.lower() and f.endswith(".txt") for f in all_files)
    has_environment_yml = any(
        f.lower() in ("environment.yml", "environment.yaml") or
        f.lower().endswith("/environment.yml") or
        f.lower().endswith("/environment.yaml")
        for f in all_files
    )
    has_dockerfile = any(Path(f).name == "Dockerfile" for f in all_files)
    has_setup_py = any(f.endswith("setup.py") for f in all_files)
    has_pyproject = any(f.endswith("pyproject.toml") for f in all_files)

    # Checkpoint files bundled in repo (unusual but possible)
    bundled_checkpoints = [
        f for f in all_files if Path(f).suffix.lower() in CHECKPOINT_EXTS
    ][:20]

    # Files suggesting precomputed / cached results
    precomputed_warning = [
        f for f in all_files
        if Path(f).suffix.lower() in PRECOMPUTED_EXTS
        and any(p in Path(f).stem.lower() for p in PRECOMPUTED_NAMES)
    ][:20]

    return {
        "repo_path": str(repo_path),
        "num_files": len(all_files),
        "has_requirements": has_requirements,
        "has_environment_yml": has_environment_yml,
        "has_dockerfile": has_dockerfile,
        "has_setup_py": has_setup_py,
        "has_pyproject": has_pyproject,
        "readme_files": readme_files[:10],
        "candidate_eval_files": _find_by_keywords(python_files, EVAL_KEYWORDS),
        "candidate_demo_files": _find_by_keywords(python_files, DEMO_KEYWORDS),
        "candidate_train_files": _find_by_keywords(python_files, TRAIN_KEYWORDS),
        "candidate_config_files": _find_by_keywords(yaml_files, CONFIG_KEYWORDS) + yaml_files[:20],
        "candidate_shell_scripts": _find_by_keywords(shell_files, EVAL_KEYWORDS + DEMO_KEYWORDS),
        "bundled_checkpoints": bundled_checkpoints,
        "precomputed_warning_files": precomputed_warning,
        "top_level_files": top_level[:50],
        "total_python_files": len(python_files),
        "total_yaml_files": len(yaml_files),
    }
