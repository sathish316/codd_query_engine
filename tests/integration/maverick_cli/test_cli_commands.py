"""Integration tests for CLI commands."""

import pytest
from typer.testing import CliRunner

from maverick_cli.maverick_cli.cli import app

runner = CliRunner()


@pytest.mark.integration
def test_cli_help():
    """Test CLI help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Maverick CLI" in result.stdout
    assert "get-semantic-metrics" in result.stdout
    assert "construct-promql-query" in result.stdout
    assert "construct-loki-query" in result.stdout
    assert "construct-splunk-query" in result.stdout


@pytest.mark.integration
def test_get_semantic_metrics_help():
    """Test get-semantic-metrics help."""
    result = runner.invoke(app, ["get-semantic-metrics", "--help"])
    assert result.exit_code == 0
    assert "Search for relevant metrics" in result.stdout
    assert "--limit" in result.stdout


@pytest.mark.integration
def test_construct_promql_query_help():
    """Test construct-promql-query help."""
    result = runner.invoke(app, ["construct-promql-query", "--help"])
    assert result.exit_code == 0
    assert "Generate a PromQL query" in result.stdout
    assert "--description" in result.stdout
    assert "--namespace" in result.stdout


@pytest.mark.integration
def test_construct_loki_query_help():
    """Test construct-loki-query help."""
    result = runner.invoke(app, ["construct-loki-query", "--help"])
    assert result.exit_code == 0
    assert "Generate a LogQL query" in result.stdout
    assert "--service" in result.stdout
    assert "--patterns" in result.stdout


@pytest.mark.integration
def test_construct_splunk_query_help():
    """Test construct-splunk-query help."""
    result = runner.invoke(app, ["construct-splunk-query", "--help"])
    assert result.exit_code == 0
    assert "Generate a Splunk SPL query" in result.stdout
    assert "--service" in result.stdout
    assert "--patterns" in result.stdout


@pytest.mark.integration
def test_metrics_subcommand_help():
    """Test metrics subcommand help."""
    result = runner.invoke(app, ["metrics", "--help"])
    assert result.exit_code == 0
    assert "Metrics operations" in result.stdout


@pytest.mark.integration
def test_logs_subcommand_help():
    """Test logs subcommand help."""
    result = runner.invoke(app, ["logs", "--help"])
    assert result.exit_code == 0
    assert "Logs operations" in result.stdout
