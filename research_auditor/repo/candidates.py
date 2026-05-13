from pathlib import Path


def read_candidate_snippets(repo_path: Path, candidate_files: list[str], max_lines: int = 80) -> str:
    parts = []
    for rel in candidate_files[:5]:
        p = repo_path / rel
        if not p.exists():
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()[:max_lines]
            snippet = "\n".join(lines)
            parts.append(f"### {rel}\n{snippet}")
        except OSError:
            continue
    return "\n\n".join(parts) if parts else "[no candidate files readable]"
