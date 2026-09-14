"""CLI commands for managing Betteragy MCP server integration in agy."""

import typer
from rich.console import Console
from rich.panel import Panel

from betteragy.mcp.mcp_registrar import MCPRegistrar

mcp_app = typer.Typer(help="Manage Betteragy To-Do MCP server registration in agy.")
console = Console()


@mcp_app.command("install")
def install_mcp() -> None:
    """Register Betteragy To-Do MCP server in agy."""
    registrar = MCPRegistrar()
    entry = registrar.install()
    console.print(
        Panel(
            f"[bold green][ok] Betteragy To-Do MCP Server registered in agy![/]\n"
            f"[dim]Settings:[/] [cyan]{registrar.settings_path}[/]\n"
            f"[dim]Command:[/] [yellow]{entry['command']}[/]\n"
            f"[dim]Arguments:[/] [white]{' '.join(entry['args'])}[/]\n\n"
            f"[bold white]'agy' will now automatically have access to:[/]\n"
            f" - [cyan]todo_init[/]   : Initialize execution plan\n"
            f" - [cyan]todo_add[/]    : Add atomic subtask\n"
            f" - [cyan]todo_update[/] : Update task status and verification evidence\n"
            f" - [cyan]todo_list[/]   : View active task board",
            title="[~] Betteragy MCP Registration",
            border_style="green",
        )
    )


@mcp_app.command("status")
def mcp_status() -> None:
    """Check if Betteragy To-Do MCP server is registered in agy."""
    registrar = MCPRegistrar()
    stat = registrar.status()
    if stat["registered"]:
        console.print(
            Panel(
                f"[bold green][ok] Betteragy To-Do MCP Server is registered[/]\n"
                f"[dim]Settings:[/] [cyan]{stat['settings_path']}[/]\n"
                f"[dim]Command:[/] [yellow]{stat['command']}[/]\n"
                f"[dim]Args:[/] [white]{' '.join(stat.get('args', []))}[/]",
                title="[~] Betteragy MCP Status",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold yellow][!] Betteragy To-Do MCP Server is not registered[/]\n"
                f"[dim]To register, run:[/] [cyan]betteragy mcp install[/]",
                title="[~] Betteragy MCP Status",
                border_style="yellow",
            )
        )


@mcp_app.command("uninstall")
def uninstall_mcp() -> None:
    """Unregister Betteragy To-Do MCP server from agy."""
    registrar = MCPRegistrar()
    if registrar.uninstall():
        console.print("[bold yellow][ok] Unregistered Betteragy To-Do MCP Server from agy.[/]")
    else:
        console.print("[dim]Server was not registered.[/]")
