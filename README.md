# Overview

Maverick is a Text2SQL Engine that can be used by AI Agents and Humans to query Databases (MySQL, Postgres, Neo4j etc) and Observability systems (Prometheus, Loki, Splunk etc)

# Architecture

Maverick Text2SQL Engine Architecture is an extension of a previous Hackday Text2SQL project by the authors called [Maverick](https://github.com/sathish316/maverick) and other Text2SQL Engines in the industry like [Uber QueryGPT](https://www.uber.com/en-IN/blog/query-gpt/), [Flipkart PlatoAI](https://blog.flipkart.tech/plato-ai-revolutionising-flipkarts-data-interaction-with-natural-language-081644ac6b16) etc.

<img src="MaverickArchitecture.drawio.png" alt="Maverick Architecture" width="100%">

# Usecases

Maverick Text2SQL Engine can be used for the following usecases:
- Querying Metrics and troubleshooting Oncall/Production issues from Coding Agents or Custom Agents
- Querying Logs and troubleshooting Oncall/Production issues from Coding Agents or Custom Agents
- Querying Relational databases in Natural language
- Querying Graph databases in Natural language

See the companion repo [Maverick AgentSkills Examples](https://github.com/sathish316/maverick_agentskills_examples) for more details on how to use Maverick as a Skill or MCP server.

# MCP Tools

**Maverick Tools:**
| Tool | Description |
|------|-------------|
| `search_relevant_metrics` | Semantic search to find metrics relevant to a problem or textual query description |
| `construct_promql_query` | Generate valid PromQL query from metrics query intent |
| `construct_logql_query` | Generate valid LogQL query for Loki from log query intent |
| `construct_splunk_query` | Generate valid Splunk SPL query from log query intent |

# Getting started with Maverick using AgentSkills

AgentSkills is a portable standard released by Anthropic for packaging AI Skills as a combination of Prompt, Resources, Scripts, MCP servers - https://agentskills.io/home. It is supported by Claude Code, Codex CLI, Cursor etc.

To use Maverick as a Skill from Claude Code and other Coding agents, see the companion repo [Maverick AgentSkills Examples](https://github.com/sathish316/maverick_agentskills_examples) for examples:
- [Using Maverick Skills for Metrics analysis](https://github.com/sathish316/maverick_agentskills_examples/blob/main/doc/USING_MAVERICK_SKILLS_FROM_CLAUDE_CODE_FOR_METRICS_AND_LOGS_ANALYSIS.md)
- [Using Maverick Skills for Logs analysis](https://github.com/sathish316/maverick_agentskills_examples/blob/main/doc/USING_MAVERICK_SKILLS_FROM_CLAUDE_CODE_FOR_METRICS_AND_LOGS_ANALYSIS.md)
- Using Maverick Skills for Database queries #TOLINK

Demo video for LogAnalyzer skill - https://youtu.be/T9wKbCRUHMI

<p align="center">
  <a href="https://youtu.be/T9wKbCRUHMI">
    <img src="https://img.youtube.com/vi/T9wKbCRUHMI/0.jpg" />
  </a>
</p>

Demo video for MetricAnalyzer skill - TODO

# Getting started with Maverick using MCP

Add the following to your `mcp.json` file in Cursor or ClaudeCode or any AI app that supports MCP:

```json
{
    "mcpServers": {
        "maverick": {
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "/path/to/maverick_query_engine",
                "python",
                "-m",
                "maverick_mcp_server.server"
            ],
            "env": {
                "PYTHONPATH": "/path/to/maverick_query_engine"
            }
        }
    }
}
```

Once Maverick MCP server is added, see the following docs for examples:
- [Using Maverick MCP server for Metrics analysis](https://github.com/sathish316/maverick_agentskills_examples/blob/main/doc/USING_MAVERICK_MCP_FROM_CURSOR_FOR_METRICS_AND_LOGS_ANALYSIS.md)
- [Using Maverick MCP server for Logs analysis](https://github.com/sathish316/maverick_agentskills_examples/blob/main/doc/USING_MAVERICK_MCP_FROM_CURSOR_FOR_METRICS_AND_LOGS_ANALYSIS.md)
- Using Maverick MCP server for Database queries #TOLINK

# Installation

1. Prerequisites

Maverick uses Redis for storing Schema metadata and a Vector database (ChromaDB) for storing Semantic metadata. Redis and ChromaDB can be installed using Docker compose

$ docker-compose up -d

2. API tokens for LLM providers

Maverick uses OpenAI or Anthropic API tokens for LLM providers. Set any of these environment variables:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY

To use Maverick with OpenRouter or custom AI Gateways, please refer to the HOW-TOs

3. Initialize config

Setup maverick config file for Text2SQL generation options and customizing the options:

```bash
# setup maverick config for MCP
mkdir -p ~/.maverick
cp maverick_engine/config/config.sample.yml ~/.maverick/config.yml
cp -r maverick_engine/prompts ~/.maverick/

# setup maverick config for Tests/Evals
mkdir -p ~/.maverick_test
cp tests/config/config.test.yml ~/.maverick_test/config.yml
```

4. Install dependencies

Maverick uses uv for package management. Install dependencies using uv

```bash
uv sync
```

It additionally uses [Opus Agents](https://github.com/sathish316/opus_agents) for Agentic capabilities. Install Opus Agents before proceeding. TOFIX - this step will be replaced with a direct PyPi installation.

```bash
# Setup opus_agents in a sibling director of maverick
cd ../

# build opus_agents
git clone git@github.com:sathish316/opus_agents.git
cd opus_agents
uv sync
uv run python -m build

# add opus_agents dependency to maverick_query_engine
cd ../maverick_query_engine
uv sync
```

5. Run tests

Maverick query engine comes with several comprehensive unit, integration, eval tests to ensure the quality of Text2SQL generation. Before using Maverick be sure to run atleast a subset of these tests:

```bash
# run unit tests
uv run pytest
# or
uv run python -m pytest

# run PromQL query generation tests to verify E2E generation
uv run pytest -m integration_querygen_evals "tests/integration/evals/test_promql_querygen_evals_integration.py::TestPromQLQueryGenEvalsIntegration::test_promql_query_generation_scenarios[scenario_1_counter_with_rate]" -s -v --log-cli-level=INFO
```

6. Start Maverick Service

Maverick MCP server uses a REST service for Query generation. Start the service using:

```bash
# Start service on default port 2840
uv run uvicorn maverick_service.main:app --host 0.0.0.0 --port 2840 --reload

# Optimize the service using uvloop
uv run python -m compileall .
uv pip install uvloop
uv run uvicorn maverick_service.main:app --host 0.0.0.0 --port 2840 --loop uvloop
```

Optionally, you can setup AI Observability using [Logfire](https://pydantic.dev/logfire) for the Service. This is essential for development and debugging Query generation.

7. Follow the MCP or AgentSkills guides to use Maverick from your favourite AI tools - ClaudeCode or Codex or Cursor.

# Development

Maverick Query engine is built using Python, uv, FastAPI, FastMCP, PydanticAI.

To build and test Maverick Query engine, run the following commands:
```
# install datastore dependencies
docker-compose up -d

# install dependencies
uv sync

# run unit tests
uv run pytest -v -s

# run integration tests
uv run pytest -v -s -m integration

# run integration tests that make LLM calls
uv run pytest -v -s -m integration_llm
```

# Evals

Maverick query engine has a Text2SQL Eval suite to validate the quality of Intent to Query generation. To run evals:

```bash
# run all evals
uv run pytest -m integration_querygen_evals -s -v

# run eval suites for specific query languages
uv run pytest -m integration_querygen_evals tests/integration/evals/test_promql_querygen_evals_integration.py -s -v

uv run pytest -m integration_querygen_evals tests/integration/evals/test_logql_querygen_evals_integration.py -s -v

uv run pytest -m integration_querygen_evals tests/integration/evals/test_spl_querygen_evals_integration.py -s -v
```

See Evals README.md for more details on QueryGen evalsuite.

# Contributing

1. Fork and create a Pull request to contribute features or capabilities

2. Github Issues and Discord Channel can be used for Maverick discussions - #TOLINK

3. Companion repo [Maverick AgentSkills Examples](https://github.com/sathish316/maverick_agentskills_examples) can be used for applications of Maverick for Database querying, Metrics/Logs analysis for AI driven Oncall Troubleshooting and more.

# License

MIT License - see the [LICENSE](LICENSE) file for details

