"""Main CLI entry point for Codd CLI."""

import typer
from rich.console import Console

from codd_cli.codd_cli.commands import metrics, logs

# Create main app
app = typer.Typer(
    name="codd",
    help="Codd CLI - CLI for Codd query engine",
    no_args_is_help=True,
    add_completion=False,
)

# Create console for rich output
console = Console()

# Add command modules
app.add_typer(metrics.app, name="metrics", help="Metrics operations")
app.add_typer(logs.app, name="logs", help="Logs operations")

# Add top-level commands for convenience (backwards compatibility)
app.command(name="get-semantic-metrics")(metrics.get_semantic_metrics)
app.command(name="construct-promql-query")(metrics.construct_promql_query)
app.command(name="construct-loki-query")(logs.construct_loki_query)
app.command(name="construct-splunk-query")(logs.construct_splunk_query)


@app.callback()
def main():
    """
    Codd CLI - CLI for Codd query engine.

    Use --help with any command to see detailed usage information.
    """
    pass


if __name__ == "__main__":
    app()
