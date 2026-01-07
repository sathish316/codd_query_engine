"""
PromQL validator pipeline that chains syntax, schema, and semantics validators.

This module provides a complete validation pipeline for PromQL queries that
validates syntax, schema, and semantics in sequence.
"""

import logging
from maverick_engine.validation_engine.metrics.validation_result import (
    ValidationResult,
    ValidationResultList,
)
from maverick_engine.validation_engine.metrics.syntax.metrics_syntax_validator import (
    MetricsSyntaxValidator,
)
from maverick_engine.validation_engine.metrics.schema.metrics_schema_validator import (
    MetricsSchemaValidator,
)
from maverick_engine.validation_engine.metrics.semantics.metrics_semantics_validator import (
    MetricsSemanticsValidator,
)
from maverick_engine.validation_engine.metrics.validator import Validator
from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


logger = logging.getLogger(__name__)


class PromQLValidator(Validator[ValidationResultList]):
    """
    Complete validation pipeline for PromQL queries.

    Runs all enabled validation stages and returns aggregated results:
    1. Syntax validation - validates PromQL grammar correctness
    2. Schema validation - validates that metrics exist in the namespace
    3. Semantics validation - validates that query matches original intent
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager = None,
        syntax_validator: MetricsSyntaxValidator = None,
        schema_validator: MetricsSchemaValidator = None,
        semantics_validator: MetricsSemanticsValidator = None,
    ):
        """
        Initialize the PromQL validator pipeline.

        Args:
            config_manager: ConfigManager for semantics validation (required if enable_semantics=True)
            instructions_manager: InstructionsManager for semantics validation (required if enable_semantics=True)
            syntax_validator: MetricsSyntaxValidator for syntax validation
            schema_validator: MetricsSchemaValidator for schema validation
            semantics_validator: MetricsSemanticsValidator for semantics validation
        """
        # Store dependencies
        self._config_manager = config_manager
        self._instructions_manager = instructions_manager
        self._syntax_validator = syntax_validator
        self._schema_validator = schema_validator
        self._semantics_validator = semantics_validator

    def validate(
        self, namespace: str, query: str, intent: MetricsQueryIntent = None, **kwargs
    ) -> ValidationResultList:
        """
        Validate a PromQL query through the complete pipeline.

        Runs all enabled validation stages and collects all errors.
        Returns ValidationResultList with same interface as ValidationResult.

        Args:
            namespace: Namespace for schema validation (required if schema validation enabled)
            query: The PromQL query string to validate
            intent: Original query intent for semantic validation (optional)
            **kwargs: Additional keyword arguments

        Returns:
            ValidationResultList: Aggregated results from all validation stages
        """
        # Read validation configuration
        syntax_enabled = self._config_manager.get_setting("mcp_config.metrics.promql.validation.syntax.enabled", True)
        schema_enabled = self._config_manager.get_setting("mcp_config.metrics.promql.validation.schema.enabled", True)
        semantics_enabled = self._config_manager.get_setting("mcp_config.metrics.promql.validation.semantics.enabled", True)

        results = []

        # Stage 1: Syntax validation
        if syntax_enabled and self._syntax_validator:
            syntax_result = self._syntax_validator.validate(query)
            results.append(syntax_result)
            if not syntax_result.is_valid:
                logger.warning(f"Syntax validation failed: {syntax_result.error}")
        else:
            logger.info("Syntax validation skipped (disabled in config)")

        # Stage 2: Schema validation
        if schema_enabled and self._schema_validator:
            schema_result = self._schema_validator.validate(namespace, query)
            results.append(schema_result)
            if not schema_result.is_valid:
                logger.warning(f"Schema validation failed: {schema_result.error}")
        else:
            logger.info("Schema validation skipped (disabled in config)")

        # Stage 3: Semantics validation (if intent provided and validator available)
        if semantics_enabled and intent and self._semantics_validator:
            semantics_result = self._semantics_validator.validate(intent, query)
            results.append(semantics_result)
            if not semantics_result.is_valid:
                logger.warning("Semantic validation failed")
        else:
            if not semantics_enabled:
                logger.info("Semantics validation skipped (disabled in config)")

        # Return aggregated results (if no validators ran, return empty list which is valid)
        return ValidationResultList(results=results if results else [ValidationResult(is_valid=True)])
