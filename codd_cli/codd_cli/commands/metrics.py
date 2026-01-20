"""Metrics commands for Codd CLI."""

import json
import typer
from rich.console import Console
from rich.table import Table
from typing import Optional

from codd_lib.client import CoddClient
from codd_lib.config import CoddConfig
from codd_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent

app = typer.Typer(help="Metrics operations")
console = Console()


def get_client(config_path: Optional[str] = None) -> CoddClient:
    """Get or create a Codd client."""
    if config_path:
        config = CoddConfig(config_path=config_path)
    else:
        config = CoddConfig()
    return CoddClient(config)


@app.command()
def get_semantic_metrics(
    query: str = typer.Argument(..., help="Natural language search query"),
    limit: int = typer.Option(5, help="Maximum number of metrics to return"),
    config_path: Optional[str] = typer.Option(
        None, "--config", help="Path to config file"
    ),
):
    """
    Search for relevant metrics using semantic search.

    Example:
        codd get-semantic-metrics "API experiencing high latency" --limit 5
    """
    try:
        client = get_client(config_path)
        results = client.metrics.search_relevant_metrics(query, limit=limit)

        if not results:
            console.print("[yellow]No metrics found matching your query.[/yellow]")
            return

        # Display results in a table
        table = Table(title=f"Semantic Search Results (Top {len(results)})")
        table.add_column("Metric Name", style="cyan", no_wrap=True)
        table.add_column("Score", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Category", style="blue")

        for result in results:
            table.add_row(
                result["metric_name"],
                f"{result['similarity_score']:.3f}",
                result.get("description", "")[:50] + "...",
                result.get("category", ""),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def construct_promql_query(
    description: str = typer.Option(..., help="Query description"),
    namespace: str = typer.Option(..., help="Prometheus namespace"),
    metric_name: Optional[str] = typer.Option(None, help="Specific metric name"),
    aggregation: Optional[str] = typer.Option(
        None, help="Aggregation function (e.g., rate, sum, avg)"
    ),
    group_by: Optional[str] = typer.Option(
        None, help="Labels to group by (comma-separated)"
    ),
    filters: Optional[str] = typer.Option(
        None, help='Label filters as JSON (e.g., \'{"status": "500"}\')'
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", help="Path to config file"
    ),
):
    """
    Generate a PromQL query from a query intent.

    Example:
        codd construct-promql-query \\
          --description "API error rate" \\
          --namespace production \\
          --metric-name http_requests_total \\
          --aggregation rate \\
          --filters '{\"status\": \"500\"}'
    """
    try:
        # Parse filters if provided
        filters_dict = json.loads(filters) if filters else None

        # Parse group_by if provided
        group_by_list = [g.strip() for g in group_by.split(",")] if group_by else None

        # Create intent
        intent = MetricsQueryIntent(
            description=description,
            namespace=namespace,
            metric_name=metric_name,
            aggregation=aggregation,
            group_by=group_by_list,
            filters=filters_dict,
        )

        # Generate query
        client = get_client(config_path)
        result = client.metrics.construct_promql_query(intent)

        if result.success:
            console.print("\n[green]✓[/green] Query generated successfully!\n")
            console.print("[cyan]Query:[/cyan]")
            console.print(f"  {result.query}\n")
        else:
            console.print(f"[red]✗[/red] Query generation failed: {result.error}\n")
            raise typer.Exit(code=1)

    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing filters JSON:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
