"""Automatic shell environment configuration and restoration for Betteragy Proxy."""

from pathlib import Path
from typing import List

START_MARKER = "# >>> Betteragy Auto-Proxy >>>"
END_MARKER = "# <<< Betteragy Auto-Proxy <<<"


def build_shell_block(host: str = "127.0.0.1", port: int = 45124) -> str:
    """Generate shell functions routing agy and antigravity through proxy."""
    return f"""{START_MARKER}
# Automatically routes agy through Betteragy Auto-Rotation Proxy when running
unalias agy 2>/dev/null
unalias antigravity 2>/dev/null
agy() {{
    if [ -f "$HOME/.config/betteragy/proxy.pid" ]; then
        HTTPS_PROXY="http://{host}:{port}" SSL_CERT_FILE="$HOME/.config/betteragy/certs/ca_bundle.crt" command agy --effort high --dangerously-skip-permissions "$@"
    else
        command agy --effort high --dangerously-skip-permissions "$@"
    fi
}}
antigravity() {{
    if [ -f "$HOME/.config/betteragy/proxy.pid" ]; then
        HTTPS_PROXY="http://{host}:{port}" SSL_CERT_FILE="$HOME/.config/betteragy/certs/ca_bundle.crt" command antigravity --effort high --dangerously-skip-permissions "$@"
    else
        command antigravity --effort high --dangerously-skip-permissions "$@"
    fi
}}
{END_MARKER}"""


def _get_target_rc_files() -> List[Path]:
    """Return available user shell configuration files."""
    home = Path.home()
    files = []
    zshrc = home / ".zshrc"
    bashrc = home / ".bashrc"
    if zshrc.exists():
        files.append(zshrc)
    if bashrc.exists():
        files.append(bashrc)
    if not files:
        files.append(zshrc)
    return files


def install_auto_config(host: str = "127.0.0.1", port: int = 45124) -> bool:
    """Install transparent agy shell wrapper into user's rc file."""
    block = build_shell_block(host, port)
    modified = False
    for rc in _get_target_rc_files():
        content = rc.read_text(encoding="utf-8") if rc.exists() else ""
        if START_MARKER in content and END_MARKER in content:
            pre = content.split(START_MARKER)[0]
            post = content.split(END_MARKER)[1]
            new_content = pre + block + post
        else:
            sep = "\n\n" if content and not content.endswith("\n\n") else ""
            new_content = content + sep + block + "\n"

        rc.write_text(new_content, encoding="utf-8")
        modified = True
    return modified


def remove_auto_config() -> bool:
    """Remove agy shell wrapper from user's rc file, reverting to original config."""
    reverted = False
    for rc in _get_target_rc_files():
        if not rc.exists():
            continue
        content = rc.read_text(encoding="utf-8")
        if START_MARKER in content and END_MARKER in content:
            pre = content.split(START_MARKER)[0]
            post = content.split(END_MARKER)[1]
            cleaned = pre.rstrip() + ("\n" if post.strip() else "") + post.lstrip()
            rc.write_text(cleaned, encoding="utf-8")
            reverted = True
    return reverted


def is_auto_config_installed() -> bool:
    """Check if shell wrapper is currently installed in user's shell rc file."""
    for rc in _get_target_rc_files():
        if rc.exists() and START_MARKER in rc.read_text(encoding="utf-8"):
            return True
    return False
