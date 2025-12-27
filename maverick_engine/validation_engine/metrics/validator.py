from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from maverick_engine.validation_engine.metrics.validation_result import ValidationResult

TValidationResult = TypeVar("TValidationResult", bound=ValidationResult)


class Validator(ABC, Generic[TValidationResult]):
    """
    Abstract base class for validators.
    """

    @abstractmethod
    def validate(self, namespace, query, **kwargs) -> TValidationResult:
        """
        Perform validation.

        Args:
            namespace: The namespace to validate metrics against
            query: The query string to validate
            **kwargs: Keyword arguments required for validation

        Returns:
            ValidationResult: A ValidationResult (or subclass) indicating success or failure

        Raises:
            Exception: Implementation-specific exceptions may be raised
        """
        pass
