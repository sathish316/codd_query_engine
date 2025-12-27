from maverick_engine.validation_engine.metrics.validation_result import ValidationResult


class SemanticValidationResult(ValidationResult):
    """
    Response schema for semantic validation of PromQL query intent.

    Extends the base ValidationResult with semantic-specific fields for intent matching,
    explanations, and confidence scoring.

    Compares the original query intent with the actual behavior of the generated query
    to determine if they match semantically.

    Attributes:
        is_valid: Inherited from ValidationResult - True if intent matches (intent_match=True)
        error: Inherited from ValidationResult - Optional error message
        intent_match: Whether the query fully matches the original intent
        partial_match: Whether the query partially matches the intent
        explanation: Detailed explanation of the semantic comparison
        original_intent_summary: Summary of what the original intent requested
        actual_query_behavior: Description of what the query actually does
    """

    intent_match: bool
    partial_match: bool
    explanation: str
    original_intent_summary: str
    actual_query_behavior: str

    def __init__(self, **data):
        """Initialize and set is_valid based on intent_match."""
        # Set is_valid based on intent_match if not explicitly provided
        data["is_valid"] = data.get("intent_match", False) or data.get(
            "partial_match", False
        )
        super().__init__(**data)

    @classmethod
    def success(cls) -> "SemanticValidationResult":
        """Create a successful validation result."""
        return SemanticValidationResult(
            intent_match=True,
            partial_match=False,
            explanation="Query matches intent",
            original_intent_summary="Rate of counter",
            actual_query_behavior="Calculates rate",
        )
