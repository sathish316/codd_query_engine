"""Health checking utility for fault simulation tests."""

import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class HealthChecker:
    """Checks service health and validates fault presence."""

    def __init__(self, base_url: str):
        """
        Initialize health checker.

        Args:
            base_url: Base URL of the service
        """
        self.base_url = base_url.rstrip("/")

    def check_health(self, endpoint: str = "/health", timeout: int = 5) -> bool:
        """
        Check if service health endpoint is responding.

        Args:
            endpoint: Health check endpoint
            timeout: Request timeout in seconds

        Returns:
            True if service is healthy
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=timeout)
            is_healthy = response.status_code == 200
            logger.info(f"Health check: {url} -> {response.status_code}")
            return is_healthy
        except requests.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return False

    def check_readiness(self, endpoint: str = "/ready", timeout: int = 5) -> dict:
        """
        Check if service is ready.

        Args:
            endpoint: Readiness check endpoint
            timeout: Request timeout in seconds

        Returns:
            Readiness status dictionary
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=timeout)
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            return {
                "ready": response.status_code == 200,
                "status_code": response.status_code,
                "data": data,
            }
        except requests.RequestException as e:
            logger.error(f"Readiness check failed: {e}")
            return {"ready": False, "error": str(e)}

    def validate_fault_present(
        self,
        fault_type: str,
        endpoint: str = "/ready",
        timeout: int = 5
    ) -> bool:
        """
        Validate that a fault is actually present in the system.

        Args:
            fault_type: Type of fault to validate
            endpoint: Endpoint to check
            timeout: Request timeout

        Returns:
            True if fault is detected
        """
        logger.info(f"Validating fault presence: {fault_type}")

        if fault_type == "redis_unavailable":
            return self._validate_redis_unavailable(endpoint, timeout)
        else:
            logger.warning(f"No validation method for fault type: {fault_type}")
            return False

    def _validate_redis_unavailable(self, endpoint: str, timeout: int) -> bool:
        """Validate Redis is unavailable by checking readiness endpoint."""
        readiness = self.check_readiness(endpoint, timeout)

        if not readiness.get("ready"):
            logger.info("Service reports not ready - fault likely present")
            return True

        # Check if Redis is specifically mentioned as disconnected
        data = readiness.get("data", {})
        if isinstance(data, dict):
            redis_status = data.get("redis")
            if redis_status in ["disconnected", "not configured"]:
                logger.info(f"Redis status: {redis_status} - fault validated")
                return True

        logger.warning("Could not validate Redis fault presence")
        return False

    def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        timeout: int = 5,
        **kwargs
    ) -> Optional[requests.Response]:
        """
        Make an HTTP request to the service.

        Args:
            endpoint: Endpoint to request
            method: HTTP method
            timeout: Request timeout
            **kwargs: Additional arguments for requests

        Returns:
            Response object or None if failed
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
