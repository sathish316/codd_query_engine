"""Docker compose management for fault simulation tests."""

import subprocess
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DockerManager:
    """Manages Docker Compose services for fault simulation tests."""

    def __init__(self, compose_file: str, project_name: str = "faultsim"):
        """
        Initialize Docker manager.

        Args:
            compose_file: Path to docker-compose.yml file
            project_name: Docker Compose project name
        """
        self.compose_file = Path(compose_file)
        self.project_name = project_name
        self.base_cmd = [
            "docker-compose",
            "-f", str(self.compose_file),
            "-p", self.project_name,
        ]

    def start_services(self, services: Optional[list[str]] = None, detach: bool = True) -> bool:
        """
        Start Docker Compose services.

        Args:
            services: List of service names to start (None for all)
            detach: Run in detached mode

        Returns:
            True if services started successfully
        """
        cmd = self.base_cmd + ["up"]
        if detach:
            cmd.append("-d")
        if services:
            cmd.extend(services)

        logger.info(f"Starting services: {services or 'all'}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                logger.info("Services started successfully")
                return True
            else:
                logger.error(f"Failed to start services: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Timeout starting services")
            return False
        except Exception as e:
            logger.error(f"Error starting services: {e}")
            return False

    def stop_services(self, services: Optional[list[str]] = None) -> bool:
        """
        Stop Docker Compose services.

        Args:
            services: List of service names to stop (None for all)

        Returns:
            True if services stopped successfully
        """
        cmd = self.base_cmd + ["stop"]
        if services:
            cmd.extend(services)

        logger.info(f"Stopping services: {services or 'all'}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                logger.info("Services stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop services: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error stopping services: {e}")
            return False

    def cleanup(self, volumes: bool = False) -> bool:
        """
        Clean up Docker Compose environment.

        Args:
            volumes: Also remove volumes

        Returns:
            True if cleanup successful
        """
        cmd = self.base_cmd + ["down"]
        if volumes:
            cmd.append("-v")

        logger.info("Cleaning up Docker environment")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                logger.info("Cleanup successful")
                return True
            else:
                logger.error(f"Cleanup failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return False

    def wait_for_healthy(self, service: str, timeout: int = 120, interval: int = 5) -> bool:
        """
        Wait for a service to become healthy.

        Args:
            service: Service name
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds

        Returns:
            True if service is healthy
        """
        logger.info(f"Waiting for {service} to become healthy (timeout: {timeout}s)")
        start_time = time.time()

        while time.time() - start_time < timeout:
            cmd = self.base_cmd + ["ps", service]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if "Up" in result.stdout:
                    logger.info(f"{service} is healthy")
                    return True
            except Exception as e:
                logger.debug(f"Health check error: {e}")

            time.sleep(interval)

        logger.error(f"{service} did not become healthy within {timeout}s")
        return False

    def get_logs(self, service: str, tail: int = 100) -> str:
        """
        Get logs from a service.

        Args:
            service: Service name
            tail: Number of lines to retrieve

        Returns:
            Service logs
        """
        cmd = self.base_cmd + ["logs", "--tail", str(tail), service]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return ""
