"""Logs-related MCP tools."""

import json


async def construct_logql_query(log_query_intent: str) -> str:
    """Generate a valid LogQL query from log query intent.

    Args:
        log_query_intent: JSON string with log query intent containing:
                        - description: Query description
                        - backend: Must be "loki"
                        - service: Service name
                        - patterns: List of log patterns (e.g., [{"pattern": "error", "level": "error"}])
                        - default_level: (optional) Default log level
                        - limit: (optional) Max results (default: 200)
                        - namespace: (optional) Kubernetes namespace

    Returns:
        JSON string with generated LogQL query and metadata.

    Example input:
        {
          "description": "Find error logs in payments service",
          "backend": "loki",
          "service": "payments",
          "patterns": [{"pattern": "error", "level": "error"}],
          "limit": 100
        }

    Example output:
        {
          "query": "{service=\"payments\"} |~ \"error\" | level=\"error\"",
          "backend": "loki",
          "success": true
        }
    """
    try:
        from maverick_engine.querygen_engine.logs.imports import LogQueryIntent
        from maverick_engine.querygen_engine.agent.logs.logql_query_generator_agent import (
            LogQLQueryGeneratorAgent,
        )
        from maverick_engine.validation_engine.logs.logql_imports import (
            LogQueryValidator,
            LogQLSyntaxValidator,
        )
        from maverick_engine.agent_imports import ConfigManager, InstructionsManager
        from maverick_engine.utils.file_utils import expand_path
    except ImportError as e:
        return json.dumps(
            {
                "error": f"Query generation dependencies not available: {e}",
                "query": "",
                "success": False,
            }
        )

    try:
        # Parse intent
        intent_data = json.loads(log_query_intent)

        # Ensure backend is loki
        if intent_data.get("backend") != "loki":
            intent_data["backend"] = "loki"

        intent = LogQueryIntent(**intent_data)

        # Initialize components
        config_manager = ConfigManager(expand_path("$HOME/.maverick"), "config.yml")
        instructions_manager = InstructionsManager()
        validator = LogQueryValidator(
            syntax_validators={"loki": LogQLSyntaxValidator()}
        )

        # Create agent and generate query
        agent = LogQLQueryGeneratorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            log_query_validator=validator,
        )

        result = agent.generate_query(intent)

        return json.dumps(
            {
                "query": result.query,
                "backend": "loki",
                "intent": intent_data,
                "success": result.success,
                "error": result.error if hasattr(result, "error") else None,
            },
            indent=2,
        )

    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON input: {e}", "query": "", "success": False}
        )
    except Exception as e:
        return json.dumps(
            {"error": str(e), "query": "", "backend": "loki", "success": False}
        )


async def construct_splunk_query(log_query_intent: str) -> str:
    """Generate a valid Splunk SPL query from log query intent.

    Args:
        log_query_intent: JSON string with log query intent containing:
                        - description: Query description
                        - backend: Must be "splunk"
                        - service: Service name
                        - patterns: List of log patterns (e.g., [{"pattern": "timeout"}])
                        - default_level: (optional) Default log level
                        - limit: (optional) Max results (default: 200)

    Returns:
        JSON string with generated Splunk SPL query and metadata.

    Example input:
        {
          "description": "Search for timeout errors in API gateway",
          "backend": "splunk",
          "service": "api-gateway",
          "patterns": [{"pattern": "timeout", "level": "error"}],
          "limit": 100
        }

    Example output:
        {
          "query": "search service=\"api-gateway\" \"timeout\" level=\"error\" | head 100",
          "backend": "splunk",
          "success": true
        }
    """
    try:
        from maverick_engine.querygen_engine.logs.imports import LogQueryIntent
        from maverick_engine.querygen_engine.agent.logs.spl_query_generator_agent import (
            SplunkSPLQueryGeneratorAgent,
        )
        from maverick_engine.validation_engine.logs.splunk_imports import (
            LogQueryValidator,
            SplunkSPLSyntaxValidator,
        )
        from maverick_engine.agent_imports import ConfigManager, InstructionsManager
        from maverick_engine.utils.file_utils import expand_path
    except ImportError as e:
        return json.dumps(
            {
                "error": f"Query generation dependencies not available: {e}",
                "query": "",
                "success": False,
            }
        )

    try:
        # Parse intent
        intent_data = json.loads(log_query_intent)

        # Ensure backend is splunk
        if intent_data.get("backend") != "splunk":
            intent_data["backend"] = "splunk"

        intent = LogQueryIntent(**intent_data)

        # Initialize components
        config_manager = ConfigManager(expand_path("$HOME/.maverick"), "config.yml")
        instructions_manager = InstructionsManager()
        validator = LogQueryValidator(
            syntax_validators={"splunk": SplunkSPLSyntaxValidator()}
        )

        # Create agent and generate query
        agent = SplunkSPLQueryGeneratorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            log_query_validator=validator,
        )

        result = agent.generate_query(intent)

        return json.dumps(
            {
                "query": result.query,
                "backend": "splunk",
                "intent": intent_data,
                "success": result.success,
                "error": result.error if hasattr(result, "error") else None,
            },
            indent=2,
        )

    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON input: {e}", "query": "", "success": False}
        )
    except Exception as e:
        return json.dumps(
            {"error": str(e), "query": "", "backend": "splunk", "success": False}
        )
