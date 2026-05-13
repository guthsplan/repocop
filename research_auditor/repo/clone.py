from pathlib import Path
from ..core.shell import run_command


def prepare_repo(
    repo_url: str | None,
    repo_local: str | None,
    run_dir: Path,
    log_path: Path,
) -> Path:
    if repo_local:
        local = Path(repo_local).expanduser().resolve()
        if not local.exists():
            raise FileNotFoundError(f"Local repo path not found: {local}")
        return local

    if not repo_url:
        raise ValueError("Either repo.url or repo.local_path must be provided.")

    dest = run_dir / "artifacts" / "repo"
    if dest.exists():
        return dest

    result = run_command(
        f"git clone --depth 1 {repo_url} {dest}",
        log_path=log_path,
        timeout=180,
    )
    if not result["success"]:
        raise RuntimeError(f"git clone failed: {result['stderr']}")

    return dest


def read_readme(repo_path: Path) -> str:
    for candidate in ["README.md", "README.rst", "README.txt", "readme.md"]:
        p = repo_path / candidate
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="ignore")
            return text[:6000]
    return ""
