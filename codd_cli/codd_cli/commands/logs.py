"""Logs commands for Codd CLI."""

import json
import typer
from rich.console import Console
from typing import Optional

from codd_lib.client import CoddClient
from codd_lib.config import CoddConfig
from codd_engine.querygen_engine.logs.structured_inputs import LogQueryIntent

app = typer.Typer(help="Logs operations")
console = Console()


def get_client(config_path: Optional[str] = None) -> CoddClient:
    """Get or create a Codd client."""
    if config_path:
        config = CoddConfig(config_path=config_path)
    else:
        config = CoddConfig()
    return CoddClient(config)


@app.command()
def construct_loki_query(
    description: str = typer.Option(..., help="Query description"),
    service: str = typer.Option(..., help="Service name"),
    patterns: str = typer.Option(
        ...,
        help='Search patterns as JSON array (e.g., \'[{"pattern": "error", "level": "error"}]\')',
    ),
    namespace: Optional[str] = typer.Option(None, help="Kubernetes namespace"),
    default_level: Optional[str] = typer.Option(None, help="Default log level"),
    limit: int = typer.Option(200, help="Maximum results"),
    config_path: Optional[str] = typer.Option(
        None, "--config", help="Path to config file"
    ),
):
    """
    Generate a LogQL query for Loki.

    Example:
        codd construct-loki-query \\
          --description "Find error logs in payments" \\
          --service payments \\
          --patterns '[{\"pattern\": \"error\", \"level\": \"error\"}]'
    """
    try:
        # Parse patterns
        patterns_list = json.loads(patterns)

        # Create intent
        intent = LogQueryIntent(
            description=description,
            backend="loki",
            service=service,
            patterns=patterns_list,
            namespace=namespace,
            default_level=default_level,
            limit=limit,
        )

        # Generate query
        client = get_client(config_path)
        result = client.logs.logql.construct_logql_query(intent)

        if result.success:
            console.print("\n[green]✓[/green] LogQL query generated successfully!\n")
            console.print("[cyan]Query:[/cyan]")
            console.print(f"  {result.query}\n")
            console.print("[dim]Backend:[/dim] loki")
        else:
            console.print(f"[red]✗[/red] Query generation failed: {result.error}\n")
            raise typer.Exit(code=1)

    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing patterns JSON:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def construct_splunk_query(
    description: str = typer.Option(..., help="Query description"),
    service: str = typer.Option(..., help="Service name"),
    patterns: str = typer.Option(
        ..., help='Search patterns as JSON array (e.g., \'[{"pattern": "timeout"}]\')'
    ),
    default_level: Optional[str] = typer.Option(None, help="Default log level"),
    limit: int = typer.Option(200, help="Maximum results"),
    config_path: Optional[str] = typer.Option(
        None, "--config", help="Path to config file"
    ),
):
    """
    Generate a Splunk SPL query.

    Example:
        codd construct-splunk-query \\
          --description "Search for timeout errors" \\
          --service api-gateway \\
          --patterns '[{\"pattern\": \"timeout\"}]'
    """
    try:
        # Parse patterns
        patterns_list = json.loads(patterns)

        # Create intent
        intent = LogQueryIntent(
            description=description,
            backend="splunk",
            service=service,
            patterns=patterns_list,
            default_level=default_level,
            limit=limit,
        )

        # Generate query
        client = get_client(config_path)
        result = client.logs.splunk.construct_spl_query(intent)

        if result.success:
            console.print(
                "\n[green]✓[/green] Splunk SPL query generated successfully!\n"
            )
            console.print("[cyan]Query:[/cyan]")
            console.print(f"  {result.query}\n")
            console.print("[dim]Backend:[/dim] splunk")
        else:
            console.print(f"[red]✗[/red] Query generation failed: {result.error}\n")
            raise typer.Exit(code=1)

    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing patterns JSON:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
