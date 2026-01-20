"""
Enum for metric name validation strategies.

This module defines the available strategies for extracting and validating
metric names from PromQL expressions.
"""

from enum import Enum


class MetricValidationStrategy(str, Enum):
    """
    Strategy for extracting and validating metric names.

    LLM: Uses LLM-based extraction to identify metric names from expressions.
         Most accurate but slower and costs API calls.

    SUBSTRING: Direct substring matching against valid metric names from Redis.
               Fast and simple, works when metric names appear as substrings in the expression.

    FUZZY: Uses fuzzy matching with rapidfuzz to find similar metric names.
           Provides "did you mean" suggestions when no exact match is found.
           Good balance between accuracy and performance.
    """

    LLM = "llm"
    SUBSTRING = "substring"
    FUZZY = "fuzzy"
