from __future__ import annotations
from pathlib import Path
from .schemas.models import AuditConfig, PaperConfig, RepoConfig, ExecutionConfig, SafetyConfig, ResourceConfig


def build_config(
    paper: str | None,
    repo: str | None,
    workdir: Path,
    mode: str,
    execute: bool,
    allow_sudo: bool,
    dataset_path: str | None,
    checkpoint_path: str | None,
    conda_path: str | None,
    run_name: str | None,
    repo_local: str | None,
    paper_pdf: str | None,
) -> AuditConfig:
    return AuditConfig(
        run_name=run_name,
        paper=PaperConfig(url=paper, pdf_path=paper_pdf),
        repo=RepoConfig(url=repo, local_path=repo_local),
        execution=ExecutionConfig(mode=mode, workdir=str(workdir), execute=execute),
        safety=SafetyConfig(allow_sudo=allow_sudo),
        resources=ResourceConfig(
            conda_path=conda_path,
            dataset_path=dataset_path,
            checkpoint_path=checkpoint_path,
        ),
    )
