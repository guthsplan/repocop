import subprocess
from pathlib import Path
from .safety import validate_command


def run_command(
    command: str,
    cwd: Path | None = None,
    log_path: Path | None = None,
    allow_sudo: bool = False,
    timeout: int = 120,
) -> dict:
    validate_command(command, allow_sudo=allow_sudo)

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        output = {
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "success": False,
        }
    except Exception as e:
        output = {
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
        }

    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"$ {command}\n")
            if output["stdout"]:
                f.write(output["stdout"] + "\n")
            if output["stderr"]:
                f.write("[stderr] " + output["stderr"] + "\n")
            f.write(f"[exit {output['returncode']}]\n\n")

    return output
