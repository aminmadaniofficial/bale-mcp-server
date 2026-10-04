"""
Command Line Interface (CLI) for Bale MCP Server.
"""

from typing import Optional
import asyncio
import os
import sys
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from bale_mcp.config import config
from bale_mcp.session_manager import session_manager
from bale_mcp.server import run_server

console = Console()


@click.group()
@click.version_option(package_name="bale-mcp-server")
def main():
    """Bale Messenger Model Context Protocol (MCP) Server CLI."""
    pass


@main.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"], case_sensitive=False),
    default="stdio",
    help="MCP transport protocol (default: stdio).",
)
@click.option(
    "--session",
    default=None,
    help="Specific session name or phone number to activate.",
)
def run(transport: str, session: Optional[str]):
    """Run the Bale MCP Server."""
    if session:
        config.ACTIVE_SESSION = session

    # Stdio transport shouldn't write non-JSON-RPC logs to stdout
    if transport == "stdio":
        import logging
        logging.getLogger().handlers = []
        logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

    run_server(transport=transport)


@main.command(name="list-sessions")
def list_sessions_cmd():
    """List all local Bale sessions stored on disk."""
    sessions = session_manager.list_sessions()

    if not sessions:
        console.print(
            Panel(
                f"[yellow]No .bale sessions found in {config.SESSIONS_DIR}.[/yellow]\n"
                "Run [bold green]bale-mcp login[/bold green] to create a new session.",
                title="Bale Sessions",
            )
        )
        return

    table = Table(title=f"Bale User Sessions ({len(sessions)} found)")
    table.add_column("Session Name", style="cyan bold")
    table.add_column("User ID", style="magenta")
    table.add_column("Name", style="green")
    table.add_column("Username", style="blue")
    table.add_column("File Path", style="dim")

    for s in sessions:
        table.add_row(
            str(s.get("session_name", "")),
            str(s.get("user_id", "") or "-"),
            str(s.get("name", "") or "-"),
            f"@{s.get('username')}" if s.get("username") else "-",
            str(s.get("file_path", "")),
        )

    console.print(table)


@main.command()
@click.option("--phone", prompt="Enter phone number (e.g. 989123456789)", help="Phone number in international format.")
def login(phone: str):
    """Interactive login to authenticate a new Bale user account."""
    clean_phone = phone.strip().replace("+", "").replace(" ", "")
    if clean_phone.startswith("0"):
        clean_phone = "98" + clean_phone[1:]

    phone_int = int(clean_phone)
    console.print(f"[cyan]Sending verification code to [bold]{phone_int}[/bold]...[/cyan]")

    async def _do_login():
        try:
            res = await session_manager.start_phone_auth(phone_int)
            if not res.get("success"):
                console.print(f"[bold red]Failed to send code:[/bold red] {res.get('message', res.get('error'))}")
                return

            tx_hash = res.get("transaction_hash")
            code = click.prompt("Enter verification code received via SMS/Bale")

            val_res = await session_manager.verify_code(code=code, transaction_hash=tx_hash)

            if val_res.get("status") == "PASSWORD_NEEDED":
                console.print("[yellow]Two-Factor Authentication is active for this account.[/yellow]")
                pwd = click.prompt("Enter 2FA Cloud Password", hide_input=True)
                val_res = await session_manager.verify_password(password=pwd, transaction_hash=tx_hash)

            if val_res.get("success"):
                console.print(
                    Panel(
                        f"[bold green]Login Successful! 🎉[/bold green]\n"
                        f"Session saved as: [cyan]{phone_int}.bale[/cyan]\n"
                        f"User ID: [magenta]{val_res.get('user_id')}[/magenta]",
                        title="Authentication Complete",
                    )
                )
            else:
                console.print(f"[bold red]Login Failed:[/bold red] {val_res.get('message', val_res.get('error'))}")
        finally:
            await session_manager.disconnect()

    asyncio.run(_do_login())


if __name__ == "__main__":
    main()
