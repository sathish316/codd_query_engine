from maverick_engine.validation_engine.metrics.validation_result import ValidationResult


class SemanticValidationResult(ValidationResult):
    """
    Response schema for semantic validation of PromQL query intent.

    Extends the base ValidationResult with semantic-specific fields for intent matching,
    explanations, and confidence scoring.

    Compares the original query intent with the actual behavior of the generated query
    to determine if they match semantically.

    Attributes:
        is_valid: Inherited from ValidationResult - True if confidence_score > threshold
        error: Inherited from ValidationResult - Optional error message
        intent_match: Whether the query fully matches the original intent
        partial_match: Whether the query partially matches the intent
        explanation: Detailed explanation of the semantic comparison
        original_intent_summary: Summary of what the original intent requested
        actual_query_behavior: Description of what the query actually does
        confidence_score: Confidence level (1-5) where:
            1 = Very Low - Query is fundamentally wrong
            2 = Low - Significant issues that need fixing
            3 = Medium - Acceptable with minor issues
            4 = High - Good match with trivial differences
            5 = Very High - Perfect match
        reasoning: Detailed reasoning for the confidence score
    """

    intent_match: bool
    partial_match: bool
    explanation: str
    original_intent_summary: str
    actual_query_behavior: str
    confidence_score: int
    reasoning: str

    def __init__(self, **data):
        """Initialize and set is_valid based on confidence_score and threshold."""
        # Set is_valid based on confidence_score and threshold if not explicitly provided
        # Default threshold is 2 (regenerate if score <= 2)
        threshold = data.pop("threshold", 2)
        data["is_valid"] = data.get("confidence_score", 1) > threshold
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
            confidence_score=5,
            reasoning="Perfect match - all aspects align with intent",
        )
