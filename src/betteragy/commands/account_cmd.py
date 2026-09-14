"""Account management subcommands: list, switch, add, remove, rotate, and cooldown."""

from typing import Optional
import typer
from rich.console import Console

from ..core.models import AccountRecord
from ..services.account_service import AccountService
from ..services.oauth_service import fetch_user_info, refresh_access_token, start_oauth_flow
from ..services.rotation_service import RotationService
from ..ui.tables import render_accounts_table
from ..ui.theme import BETTERAGY_THEME

account_app = typer.Typer(help="Manage and switch Antigravity accounts")
console = Console(theme=BETTERAGY_THEME)
acc_svc = AccountService()
rot_svc = RotationService(acc_svc)


@account_app.command("list")
def account_list():
    """List all configured Antigravity accounts and their statuses."""
    accounts = acc_svc.get_accounts()
    storage = acc_svc.get_storage()
    if not accounts:
        console.print("[yellow]No accounts found. Use 'betteragy account add' to connect an account.[/yellow]")
        raise typer.Exit(0)
    console.print(render_accounts_table(accounts, storage.active_email))


@account_app.command("switch")
def account_switch(identifier: str = typer.Argument(..., help="Account index or email")):
    """Switch active account session for agy CLI and system keyring."""
    success, msg = acc_svc.switch_account(identifier)
    if success:
        console.print(f"[bold green][ok] {msg}[/bold green]")
    else:
        console.print(f"[bold red][!] {msg}[/bold red]")
        raise typer.Exit(1)


@account_app.command("add")
def account_add(
    token: Optional[str] = typer.Option(
        None, "--token", "-t", help="Add account directly using a Google refresh_token (headless/no-browser)"
    ),
):
    """Connect a new Google/Antigravity account via browser OAuth or refresh token."""
    if token:
        console.print("[cyan]Verifying provided refresh token with Google OAuth...[/cyan]")
        try:
            tokens = refresh_access_token(token.strip())
            uinfo = fetch_user_info(tokens["access_token"])
            email = uinfo.get("email")
            if not email:
                console.print("[bold red][!] Failed to retrieve user email with provided token.[/bold red]")
                raise typer.Exit(1)
            rec = AccountRecord(
                email=email,
                name=uinfo.get("name", ""),
                picture=uinfo.get("picture", ""),
                refresh_token=token.strip(),
                access_token=tokens["access_token"],
            )
            acc_svc.add_or_update_account(rec, make_active=True)
            console.print(f"[bold green][ok] Connected and activated account via token: {rec.email}[/bold green]")
            return
        except Exception as e:
            console.print(f"[bold red][!] Invalid refresh token: {e}[/bold red]")
            raise typer.Exit(1)

    console.print("[cyan]Opening browser for Google Antigravity authentication...[/cyan]")
    res = start_oauth_flow()
    if not res:
        console.print("[red]Authentication cancelled or timed out.[/red]")
        raise typer.Exit(1)

    tokens = res["tokens"]
    uinfo = res["user_info"]
    rec = AccountRecord(
        email=uinfo["email"],
        name=uinfo.get("name", ""),
        picture=uinfo.get("picture", ""),
        refresh_token=tokens["refresh_token"],
        access_token=tokens["access_token"],
    )
    acc_svc.add_or_update_account(rec, make_active=True)
    console.print(f"[bold green][ok] Account connected and set as active: {rec.email}[/bold green]")


@account_app.command("remove")
def account_remove(identifier: str = typer.Argument(..., help="Account index or email")):
    """Remove an account from your pool."""
    ok = acc_svc.remove_account(identifier)
    if ok:
        console.print(f"[green][ok] Removed account: {identifier}[/green]")
    else:
        console.print(f"[red][!] Account not found: {identifier}[/red]")
        raise typer.Exit(1)


@account_app.command("rotate")
def account_rotate(
    strategy: Optional[str] = typer.Option(None, "--strategy", "-s", help="round-robin, least-used, sticky, random"),
    force: bool = typer.Option(False, "--force", "-f", help="Force switch even if single account"),
):
    """Rotate to the next healthy account in sequence."""
    ok, msg = rot_svc.rotate(strategy=strategy, force=force)
    if ok:
        console.print(f"[bold green][ok] {msg}[/bold green]")
    else:
        console.print(f"[bold red][!] {msg}[/bold red]")
        raise typer.Exit(1)


@account_app.command("cooldown")
def account_cooldown(hours: float = typer.Argument(4.0, help="Hours to cooldown (default: 4)")):
    """Mark the active account rate-limited and rotate to next healthy account."""
    ok, msg = rot_svc.set_cooldown(hours=hours)
    console.print(f"[yellow]{msg}[/yellow]")
    if not ok:
        raise typer.Exit(1)


@account_app.command("current")
def account_current():
    """Display the currently active account."""
    acc = acc_svc.get_active_account()
    if not acc:
        console.print("[yellow]No active account configured.[/yellow]")
        raise typer.Exit(0)
    console.print(f"Active Account: [bold green]{acc.email}[/bold green] ({acc.tier_name or acc.tier or 'Standard'})")
