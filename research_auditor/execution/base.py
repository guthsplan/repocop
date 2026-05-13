from abc import ABC, abstractmethod
from pathlib import Path
from .command_result import CommandResult


class Executor(ABC):
    @abstractmethod
    def run(
        self,
        command: str,
        cwd: Path | None = None,
        log_path: Path | None = None,
        timeout: int = 120,
    ) -> CommandResult:
        ...
