"""Daemon process control and health probing for the Betteragy local proxy."""

import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from typing import Optional
from ..core.constants import CONFIG_DIR
from .server import DEFAULT_PROXY_HOST, DEFAULT_PROXY_PORT

PID_FILE = CONFIG_DIR / "proxy.pid"
LOG_FILE = CONFIG_DIR / "proxy.log"


def _is_pid_alive(pid: int) -> bool:
    """Check if process with given PID is still alive."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _find_pid_by_port(port: int) -> Optional[int]:
    """Attempt to find PID listening on port using lsof."""
    try:
        out = subprocess.check_output(
            ["lsof", "-ti", f":{port}"],
            stderr=subprocess.DEVNULL,
            timeout=1.0,
        )
        pids = [int(p.strip()) for p in out.decode().strip().split() if p.strip().isdigit()]
        if pids:
            return pids[0]
    except Exception:
        pass
    return None


def is_port_in_use(host: str = DEFAULT_PROXY_HOST, port: int = DEFAULT_PROXY_PORT) -> bool:
    """Check if host:port is currently accepting TCP connections."""
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def get_proxy_pid() -> Optional[int]:
    """Return running proxy PID if alive, otherwise None."""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        if _is_pid_alive(pid):
            return pid
        PID_FILE.unlink(missing_ok=True)
        return None
    except (ValueError, OSError):
        PID_FILE.unlink(missing_ok=True)
        return None


def is_healthy(host: str = DEFAULT_PROXY_HOST, port: int = DEFAULT_PROXY_PORT) -> bool:
    """Probe proxy /health endpoint with 1s timeout, bypassing any environment proxies."""
    try:
        url = f"http://{host}:{port}/health"
        req = urllib.request.Request(url)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def is_proxy_running(host: str = DEFAULT_PROXY_HOST, port: int = DEFAULT_PROXY_PORT) -> bool:
    """Check if proxy daemon is alive and answering health probes."""
    pid = get_proxy_pid()
    if not pid and is_healthy(host, port):
        pid = _find_pid_by_port(port)
        if pid:
            PID_FILE.write_text(str(pid), encoding="utf-8")
    return bool(pid and is_healthy(host, port))


def _extract_last_error_from_log(max_lines: int = 25) -> str:
    """Extract recent error line from proxy.log if available."""
    if not LOG_FILE.exists():
        return ""
    try:
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in reversed(lines[-max_lines:]):
            clean = line.strip()
            if "error while attempting to bind" in clean or "address already in use" in clean.lower():
                return "Port address already in use by another process"
            if "Errno 48" in clean:
                return "Port already in use"
            if "[x]" in clean or "[ERROR]" in clean or "Error:" in clean:
                return clean.split("] ", 1)[-1] if "] " in clean else clean
    except Exception:
        pass
    return ""


def start_proxy_daemon(
    host: str = DEFAULT_PROXY_HOST,
    port: int = DEFAULT_PROXY_PORT,
    timeout_secs: float = 5.0,
) -> tuple[bool, int, str]:
    """Spawn background proxy daemon. Returns (success, pid, message)."""
    from .auto_config import install_auto_config

    pid = get_proxy_pid()
    if not pid and is_healthy(host, port):
        pid = _find_pid_by_port(port)
        if pid:
            PID_FILE.write_text(str(pid), encoding="utf-8")

    if pid and is_healthy(host, port):
        install_auto_config(host=host, port=port)
        return True, pid, f"Proxy is already running (PID: {pid}) on http://{host}:{port}"

    if is_port_in_use(host, port):
        occupied_pid = _find_pid_by_port(port)
        pid_str = f" (PID: {occupied_pid})" if occupied_pid else ""
        return (
            False,
            occupied_pid or 0,
            f"Port {port} is already in use{pid_str}. Run 'betteragy proxy stop' first",
        )

    # Sanitize env so daemon doesn't route outbound calls back to localhost proxy
    daemon_env = os.environ.copy()
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        daemon_env.pop(key, None)

    cmd = [sys.executable, "-m", "betteragy.cli", "proxy", "run", "--host", host, "--port", str(port)]
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(LOG_FILE, "a", encoding="utf-8") as out:
        proc = subprocess.Popen(cmd, stdout=out, stderr=out, env=daemon_env, start_new_session=True)

    PID_FILE.write_text(str(proc.pid), encoding="utf-8")

    # Wait for proxy to become healthy
    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        retcode = proc.poll()
        if retcode is not None:
            PID_FILE.unlink(missing_ok=True)
            err_msg = _extract_last_error_from_log()
            detail = f": {err_msg}" if err_msg else f" (exit code {retcode})"
            return False, proc.pid, f"Proxy process failed to start{detail}"

        time.sleep(0.15)
        if is_healthy(host, port):
            install_auto_config(host=host, port=port)
            return True, proc.pid, f"Proxy started on http://{host}:{port}"

    if proc.poll() is not None:
        PID_FILE.unlink(missing_ok=True)
        return False, proc.pid, f"Proxy process exited prematurely (exit code {proc.returncode})"

    return False, proc.pid, f"Proxy started (PID: {proc.pid}) but health probe timed out"


def stop_proxy_daemon() -> bool:
    """Stop running proxy daemon and revert shell auto-config. Returns True if stopped."""
    from .auto_config import remove_auto_config

    remove_auto_config()
    pid = get_proxy_pid() or _find_pid_by_port(DEFAULT_PROXY_PORT)
    if not pid:
        PID_FILE.unlink(missing_ok=True)
        return False

    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(12):
            time.sleep(0.15)
            if not _is_pid_alive(pid):
                break
        else:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
    except OSError:
        pass

    PID_FILE.unlink(missing_ok=True)
    return True
