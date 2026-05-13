from __future__ import annotations
from pathlib import Path
from typing import Optional
import typer
from .config import build_config
from .runner import run_audit

app = typer.Typer(name="research-audit", add_completion=False)


@app.command()
def run(
    paper: Optional[str] = typer.Option(None, help="Paper URL or project page URL"),
    paper_pdf: Optional[str] = typer.Option(None, help="Local path to paper PDF"),
    repo: Optional[str] = typer.Option(None, help="Git repository URL to audit"),
    repo_local: Optional[str] = typer.Option(None, help="Local path to already-cloned repo"),
    workdir: Path = typer.Option(..., help="Working directory for all run artifacts"),
    run_name: Optional[str] = typer.Option(None, help="Short name for this run (used in directory name)"),
    mode: str = typer.Option("local", help="Execution mode: local"),
    execute: bool = typer.Option(False, help="Actually run setup and eval commands (default: plan only)"),
    allow_sudo: bool = typer.Option(False, help="Allow sudo in shell commands (default: false)"),
    dataset_path: Optional[str] = typer.Option(None, help="Path to dataset required by eval"),
    checkpoint_path: Optional[str] = typer.Option(None, help="Path to model checkpoint"),
    conda_path: Optional[str] = typer.Option(None, help="Path to conda installation"),
) -> None:
    """
    Audit a research paper + repository for reproducibility.

    Example:
      research-audit run --paper https://example.com/paper \\
          --repo https://github.com/org/repo --workdir ~/audits
    """
    if not paper and not paper_pdf:
        typer.echo("Error: provide --paper (URL) or --paper-pdf (local PDF path).", err=True)
        raise typer.Exit(1)
    if not repo and not repo_local:
        typer.echo("Error: provide --repo (URL) or --repo-local (local path).", err=True)
        raise typer.Exit(1)

    config = build_config(
        paper=paper,
        repo=repo,
        workdir=workdir,
        mode=mode,
        execute=execute,
        allow_sudo=allow_sudo,
        dataset_path=dataset_path,
        checkpoint_path=checkpoint_path,
        conda_path=conda_path,
        run_name=run_name,
        repo_local=repo_local,
        paper_pdf=paper_pdf,
    )

    run_audit(config)


if __name__ == "__main__":
    app()
