from pathlib import Path

FORBIDDEN_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "mkfs",
    "shutdown",
    "reboot",
    "chmod -R 777 /",
    "dd if=",
    "> /dev/",
]

FORBIDDEN_PATH_PREFIXES = [
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/lib",
    "/boot",
    "/sys",
    "/proc",
]


def validate_command(command: str, allow_sudo: bool = False) -> None:
    if not allow_sudo and command.strip().startswith("sudo "):
        raise ValueError(f"sudo is not allowed: {command}")

    for pattern in FORBIDDEN_PATTERNS:
        if pattern in command:
            raise ValueError(f"Forbidden command pattern '{pattern}' in: {command}")


def ensure_inside_workdir(path: Path, workdir: Path) -> None:
    resolved = path.expanduser().resolve()
    wd_resolved = workdir.expanduser().resolve()
    if not str(resolved).startswith(str(wd_resolved)):
        raise ValueError(f"Path escapes workdir: {resolved} not under {wd_resolved}")


def is_safe_path(path: str) -> bool:
    for prefix in FORBIDDEN_PATH_PREFIXES:
        if path.startswith(prefix):
            return False
    return True
