"""Shell integration snippet generator for zsh/bash."""

import typer
from rich.console import Console
from rich.syntax import Syntax

from ..ui.theme import BETTERAGY_THEME

console = Console(theme=BETTERAGY_THEME)

SHELL_SNIPPET = """# Betteragy Shell Integration for Antigravity
# Add the following lines to your ~/.zshrc or ~/.bashrc:

# Wrapper to auto-rotate healthy account or run agy seamlessly
agy() {
    betteragy account rotate > /dev/null 2>&1
    command agy "$@"
}

# Quick cooldown command when rate-limit is hit
agycool() {
    betteragy account cooldown "${1:-4}"
}

# Quick alias for live dashboard
alias agydash="betteragy dashboard"
alias agyquota="betteragy quota"
alias agyusage="betteragy usage"
"""


def shell_integration_command():
    """Print shell integration aliases and wrapper functions for ~/.zshrc or ~/.bashrc."""
    syntax = Syntax(SHELL_SNIPPET, "bash", theme="monokai", line_numbers=False)
    console.print(syntax)
