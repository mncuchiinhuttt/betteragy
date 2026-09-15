"""Interactive step-by-step terminal onboarding wizard for first-run setup."""

import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..services.onboarding_service import OnboardingService
from .theme import BETTERAGY_THEME

console = Console(theme=BETTERAGY_THEME)


def _step_accounts(svc: OnboardingService, interactive: bool) -> None:
    console.print("\n[bold cyan]Step 1/5: Account Discovery & Connection[/bold cyan]")
    accs = svc.detect_and_import_accounts()
    if accs:
        table = Table(box=None, show_header=True, pad_edge=False)
        table.add_column("Status", width=8)
        table.add_column("Email", style="bold white")
        for a in accs:
            badge = "[bold green][*] Active[/]" if a.get("active") else "[dim][+] Ready[/]"
            table.add_row(badge, a["email"])
        console.print(table)
        console.print(f"[bold green][ok] Imported {len(accs)} account(s) from Keychain.[/bold green]")
    else:
        console.print("[yellow][!] No accounts detected in Keychain.[/yellow]")
        if interactive and Confirm.ask("Connect a Google account via browser OAuth now?", default=True):
            try:
                from ..services.oauth_service import OAuthService
                rec = OAuthService().login_via_browser()
                svc.acc_svc.save_account(rec, set_active=True)
                console.print(f"[bold green][ok] Connected: {rec.email}[/bold green]")
            except Exception as e:
                console.print(f"[dim]OAuth connection skipped: {e}[/dim]")


def _step_harness(svc: OnboardingService, interactive: bool) -> str:
    console.print("\n[bold cyan]Step 2/5: Deep Reasoning & Verification Harness[/bold cyan]")
    console.print("[dim]Injects elite reasoning directives, OMP invariants & verification gates into agy.[/dim]")
    profile = "strict"
    if interactive:
        choice = Prompt.ask(
            "Select reasoning harness profile: [1] Strict (Recommended), [2] Balanced",
            choices=["1", "2"],
            default="1",
        )
        profile = "strict" if choice == "1" else "balanced"
    res = svc.setup_harness(profile=profile)
    console.print(f"[bold green][ok] Installed {res['profile']} harness in agy rules & GEMINI.md[/bold green]")
    return profile


def _step_mcp(svc: OnboardingService) -> None:
    console.print("\n[bold cyan]Step 3/5: MCP Task Planning Server[/bold cyan]")
    console.print("[dim]Registers 'betteragy-todo' stdio server in ~/.gemini/config/mcp_config.json.[/dim]")
    svc.setup_mcp_server()
    console.print("[bold green][ok] Registered 'betteragy-todo' MCP server.[/bold green]")


def _step_shell(svc: OnboardingService, interactive: bool) -> None:
    console.print("\n[bold cyan]Step 4/5: Shell Alias & Autonomous Flag[/bold cyan]")
    do_alias = True
    if interactive:
        do_alias = Confirm.ask("Add 'alias agy=\"agy --effort high --dangerously-skip-permissions\"' to shell profile?", default=True)
    if do_alias:
        res = svc.setup_shell_alias()
        if res.get("already_existed"):
            console.print(f"[yellow][~] Alias already present in {res['target']}[/yellow]")
        else:
            console.print(f"[bold green][ok] Added autonomous alias to {res['target']}[/bold green]")


def _step_summary(svc: OnboardingService, profile: str) -> None:
    diag = svc.run_diagnostics()
    console.print("\n[bold cyan]Step 5/5: Verification & System Diagnostics[/bold cyan]")
    summary_lines = [
        f"[bold green][ok] Betteragy setup is complete![/bold green]\n",
        f"  [bold green][x][/] Account Pool: [bold white]{diag['accounts_count']}[/] account(s) active ({diag['active_account'] or 'None'})",
        f"  [bold green][x][/] Deep Reasoning: [bold white]Active[/] (Profile: [cyan]{diag['harness_profile']}[/])",
        f"  [bold green][x][/] MCP Planning: [bold white]Active[/] (Server: [cyan]betteragy-todo[/])",
        f"  [bold green][x][/] Shell Alias: [bold white]{'Configured' if diag['shell_alias_configured'] else 'Skipped'}[/] ({diag['target_shell_file']})",
        "\n[dim]All agy sessions will now automatically benefit from deep thinking and auto-rotation.[/dim]",
    ]
    console.print(Panel("\n".join(summary_lines), title="[~] Betteragy Ready", border_style="green"))


def run_onboarding_wizard(svc: Optional[OnboardingService] = None, interactive: bool = True) -> bool:
    """Run the 5-step onboarding wizard. Returns True on successful completion."""
    onboarding_svc = svc or OnboardingService()
    is_interactive = interactive and sys.stdin.isatty()

    welcome_text = (
        "[bold cyan]Welcome to Betteragy![/bold cyan]\n"
        "[dim]Let's configure your environment for maximum reasoning effort, multi-account rotation, and task planning.[/dim]"
    )
    console.print(Panel(welcome_text, title="[~] First-Run Setup Wizard", border_style="cyan"))

    try:
        _step_accounts(onboarding_svc, is_interactive)
        profile = _step_harness(onboarding_svc, is_interactive)
        _step_mcp(onboarding_svc)
        _step_shell(onboarding_svc, is_interactive)
        _step_summary(onboarding_svc, profile)
        onboarding_svc.mark_completed(profile=profile, notes="wizard_completed")
        if is_interactive:
            Prompt.ask("\n[bold white]Press Enter to continue to Betteragy...[/bold white]", default="")
        return True
    except KeyboardInterrupt:
        console.print("\n[yellow][!] Onboarding cancelled by user.[/yellow]")
        return False
