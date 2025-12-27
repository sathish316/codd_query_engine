"""
PromQL validator pipeline that chains syntax, schema, and semantics validators.

This module provides a complete validation pipeline for PromQL queries that
validates syntax, schema, and semantics in sequence.
"""

import logging
from maverick_engine.validation_engine.metrics.structured_outputs import ValidationResult
from maverick_engine.validation_engine.metrics.metrics_syntax_validator import MetricsSyntaxValidator
from maverick_engine.validation_engine.metrics.metrics_schema_validator import MetricsSchemaValidator
from maverick_engine.validation_engine.metrics.metrics_semantics_validator import MetricsSemanticsValidator
from maverick_engine.validation_engine.metrics.validator import Validator
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


logger = logging.getLogger(__name__)


class PromQLValidator(Validator[ValidationResult]):
    """
    Complete validation pipeline for PromQL queries.

    This pipeline chains together three validators in sequence:
    1. Syntax validation - validates PromQL grammar correctness
    2. Schema validation - validates that metrics exist in the namespace
    3. Semantics validation - validates that query matches original intent
    """

    def __init__(
        self,
        config_manager: ConfigManager = None,
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

    def validate(self, namespace, query, **kwargs) -> ValidationResult:
        """
        Validate a PromQL query through the complete pipeline.

        Args:
            namespace: Namespace for schema validation (required if schema validation enabled)
            query: The PromQL query string to validate
            **kwargs: Additional keyword arguments
        """
        # syntax validation
        result = self._syntax_validator.validate(query)
        if not result.is_valid:
            return result
        # schema validation
        result = self._schema_validator.validate(namespace, query)
        if not result.is_valid:
            return result
        # semantics validation
        result = self._semantics_validator.validate(query, namespace, **kwargs)
        if not result.is_valid:
            return result
        return result
