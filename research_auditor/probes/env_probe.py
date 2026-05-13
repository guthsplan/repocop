from pathlib import Path
from ..core.shell import run_command


def probe_environment(allow_sudo: bool, log_path: Path) -> dict:
    probes = {
        "whoami": "whoami",
        "uname": "uname -a",
        "python": "python --version 2>&1 || python3 --version 2>&1",
        "conda": "conda --version 2>&1",
        "nvcc": "nvcc --version 2>&1",
        "nvidia_smi": "nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>&1",
        "disk": "df -h --output=source,size,avail,target 2>&1 | head -10",
        "memory": "free -h 2>&1",
        "git": "git --version 2>&1",
        "docker": "docker --version 2>&1",
    }

    results = {}
    for key, cmd in probes.items():
        out = run_command(cmd, log_path=log_path)
        results[key] = out["stdout"] if out["success"] else f"[not found] {out['stderr']}"

    gpu_line = results.get("nvidia_smi", "")
    cuda_line = results.get("nvcc", "")

    return {
        "whoami": results.get("whoami", ""),
        "uname": results.get("uname", ""),
        "python": results.get("python", ""),
        "conda": results.get("conda", ""),
        "git": results.get("git", ""),
        "docker": results.get("docker", ""),
        "gpu": gpu_line or "not detected",
        "cuda": cuda_line or "not detected",
        "disk": results.get("disk", ""),
        "memory": results.get("memory", ""),
        "sudo_allowed": allow_sudo,
    }
