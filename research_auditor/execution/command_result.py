from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    success: bool
    duration_s: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)
