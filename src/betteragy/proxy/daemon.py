"""Daemon process control and health probing for the Betteragy local proxy."""

import os
import signal
import subprocess
import sys
import time
import urllib.request
from typing import Optional

from ..core.constants import CONFIG_DIR
from .server import DEFAULT_PROXY_HOST, DEFAULT_PROXY_PORT

PID_FILE = CONFIG_DIR / "proxy.pid"
LOG_FILE = CONFIG_DIR / "proxy.log"


def get_proxy_pid() -> Optional[int]:
    """Return running proxy PID if alive, otherwise None."""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return pid
    except (ValueError, OSError):
        PID_FILE.unlink(missing_ok=True)
        return None


def is_healthy(host: str = DEFAULT_PROXY_HOST, port: int = DEFAULT_PROXY_PORT) -> bool:
    """Probe proxy /health endpoint with 1s timeout."""
    try:
        url = f"http://{host}:{port}/health"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def is_proxy_running(host: str = DEFAULT_PROXY_HOST, port: int = DEFAULT_PROXY_PORT) -> bool:
    """Check if proxy daemon is alive and answering health probes."""
    pid = get_proxy_pid()
    return bool(pid and is_healthy(host, port))


def start_proxy_daemon(
    host: str = DEFAULT_PROXY_HOST,
    port: int = DEFAULT_PROXY_PORT,
    timeout_secs: float = 3.0,
) -> tuple[bool, int, str]:
    """Spawn background proxy daemon. Returns (success, pid, message)."""
    pid = get_proxy_pid()
    if pid and is_healthy(host, port):
        return True, pid, f"Proxy is already running (PID: {pid}) on http://{host}:{port}"

    cmd = [sys.executable, "-m", "betteragy.cli", "proxy", "run", "--host", host, "--port", str(port)]
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(LOG_FILE, "a", encoding="utf-8") as out:
        proc = subprocess.Popen(cmd, stdout=out, stderr=out, start_new_session=True)

    PID_FILE.write_text(str(proc.pid), encoding="utf-8")

    # Wait for proxy to become healthy
    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        time.sleep(0.15)
        if is_healthy(host, port):
            return True, proc.pid, f"Proxy started on http://{host}:{port}"

    return False, proc.pid, f"Proxy started (PID: {proc.pid}) but health probe timed out"


def stop_proxy_daemon() -> bool:
    """Stop running proxy daemon. Returns True if stopped."""
    pid = get_proxy_pid()
    if not pid:
        PID_FILE.unlink(missing_ok=True)
        return False

    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(12):
            time.sleep(0.15)
            if not get_proxy_pid():
                break
    except OSError:
        pass

    PID_FILE.unlink(missing_ok=True)
    return True
