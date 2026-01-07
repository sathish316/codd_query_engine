"""Traffic generation utility for fault simulation tests."""

import time
import logging
import threading
import requests
from typing import Callable, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TrafficConfig:
    """Configuration for traffic generation."""

    url: str
    duration_minutes: int = 1
    requests_per_second: int = 10
    endpoints: Optional[list[str]] = None


class TrafficGenerator:
    """Generates HTTP traffic to a service for testing."""

    def __init__(self, config: TrafficConfig):
        """
        Initialize traffic generator.

        Args:
            config: Traffic generation configuration
        """
        self.config = config
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.request_count = 0
        self.error_count = 0
        self.endpoints = config.endpoints or ["/beers", "/health", "/ready"]

    def start(self, background: bool = True) -> bool:
        """
        Start generating traffic.

        Args:
            background: Run in background thread

        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning("Traffic generator already running")
            return False

        self.running = True
        logger.info(
            f"Starting traffic generation for {self.config.duration_minutes} minutes "
            f"at {self.config.requests_per_second} req/s"
        )

        if background:
            self.thread = threading.Thread(target=self._generate_traffic, daemon=True)
            self.thread.start()
            return True
        else:
            self._generate_traffic()
            return True

    def stop(self):
        """Stop traffic generation."""
        if self.running:
            logger.info("Stopping traffic generation")
            self.running = False
            if self.thread:
                self.thread.join(timeout=10)
            logger.info(
                f"Traffic generation stopped. "
                f"Total requests: {self.request_count}, Errors: {self.error_count}"
            )

    def _generate_traffic(self):
        """Internal method to generate traffic."""
        end_time = time.time() + (self.config.duration_minutes * 60)
        interval = 1.0 / self.config.requests_per_second

        while self.running and time.time() < end_time:
            for endpoint in self.endpoints:
                if not self.running:
                    break

                url = f"{self.config.url}{endpoint}"
                try:
                    response = requests.get(url, timeout=5)
                    self.request_count += 1

                    if response.status_code >= 400:
                        self.error_count += 1
                        logger.debug(f"Error response from {endpoint}: {response.status_code}")
                    else:
                        logger.debug(f"Success: {endpoint} -> {response.status_code}")

                except requests.RequestException as e:
                    self.error_count += 1
                    logger.debug(f"Request failed to {endpoint}: {e}")

                time.sleep(interval)

        self.running = False
        logger.info("Traffic generation completed")

    def get_stats(self) -> dict:
        """
        Get traffic generation statistics.

        Returns:
            Dictionary with request and error counts
        """
        return {
            "total_requests": self.request_count,
            "errors": self.error_count,
            "success_rate": (
                (self.request_count - self.error_count) / self.request_count * 100
                if self.request_count > 0
                else 0
            ),
        }
