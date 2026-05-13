from __future__ import annotations
import subprocess
import time
from pathlib import Path

from .base import Executor
from .command_result import CommandResult
from ..core.safety import validate_command


class LocalExecutor(Executor):
    def __init__(self, allow_sudo: bool = False):
        self.allow_sudo = allow_sudo

    def run(
        self,
        command: str,
        cwd: Path | None = None,
        log_path: Path | None = None,
        timeout: int = 120,
    ) -> CommandResult:
        validate_command(command, allow_sudo=self.allow_sudo)

        start = time.time()
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            result = CommandResult(
                command=command,
                returncode=proc.returncode,
                stdout=proc.stdout.strip(),
                stderr=proc.stderr.strip(),
                success=proc.returncode == 0,
                duration_s=round(time.time() - start, 2),
            )
        except subprocess.TimeoutExpired:
            result = CommandResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=f"Timed out after {timeout}s",
                success=False,
                duration_s=round(time.time() - start, 2),
            )
        except Exception as e:
            result = CommandResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=str(e),
                success=False,
                duration_s=round(time.time() - start, 2),
            )

        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"$ {command}\n")
                if result.stdout:
                    f.write(result.stdout + "\n")
                if result.stderr:
                    f.write("[stderr] " + result.stderr + "\n")
                f.write(f"[exit {result.returncode}] ({result.duration_s}s)\n\n")

        return result
