import os
import subprocess
from typing import Any

import psutil


def check_system_metrics() -> dict[str, Any]:
    """Return CPU utilization per core, load averages, RAM usage, and top CPU processes."""
    per_core = psutil.cpu_percent(interval=1, percpu=True)
    load_avg = os.getloadavg()
    mem = psutil.virtual_memory()

    processes: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent", "cmdline"]):
        try:
            info = proc.info
            cmd = info.get("cmdline") or []
            processes.append(
                {
                    "pid": info.get("pid"),
                    "name": info.get("name"),
                    "username": info.get("username"),
                    "cpu_percent": info.get("cpu_percent") or 0.0,
                    "memory_percent": round(info.get("memory_percent") or 0.0, 2),
                    "cmdline": " ".join(cmd[:4]),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top_processes = sorted(processes, key=lambda p: p["cpu_percent"], reverse=True)[:8]
    avg_cpu = round(sum(per_core) / len(per_core), 1) if per_core else 0.0

    return {
        "cpu_per_core_percent": per_core,
        "cpu_avg_percent": avg_cpu,
        "load_average_1m_5m_15m": [round(x, 2) for x in load_avg],
        "ram_used_percent": round(mem.percent, 1),
        "top_processes": top_processes,
    }


def inspect_process_or_logs(pid: int = 0, service_name: str = "") -> str:
    """Inspect a process by PID or fetch recent systemd journal entries for a service."""
    sections: list[str] = []

    if pid > 0:
        try:
            proc = psutil.Process(pid)
            cmdline = " ".join(proc.cmdline())
            sections.append(
                f"PID {pid} ({proc.name()}): status={proc.status()}, "
                f"threads={proc.num_threads()}, ppid={proc.ppid()}, cmd='{cmdline}'"
            )
        except Exception as exc:
            sections.append(f"Failed to inspect PID {pid}: {exc}")

    if service_name:
        res = subprocess.run(
            ["journalctl", "-u", service_name, "-n", "25", "--no-pager"],
            capture_output=True,
            text=True,
            check=False,
        )
        logs = (res.stdout or res.stderr).strip()
        sections.append(f"--- systemd logs ({service_name}) ---\n{logs}")

    return "\n".join(sections) if sections else "Provide a valid pid (> 0) or service_name."
