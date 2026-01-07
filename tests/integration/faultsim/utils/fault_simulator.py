"""Fault simulation utility for chaos engineering tests."""

import subprocess
import logging
import time
from enum import Enum
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


class FaultType(Enum):
    """Types of faults that can be simulated."""

    REDIS_UNAVAILABLE = "redis_unavailable"
    NETWORK_DELAY = "network_delay"
    CPU_STRESS = "cpu_stress"
    MEMORY_STRESS = "memory_stress"
    SERVICE_CRASH = "service_crash"


@dataclass
class FaultScenario:
    """Configuration for a fault simulation scenario."""

    fault_type: FaultType
    target_service: str
    duration_minutes: int = 5
    params: Optional[dict] = None


class FaultSimulator:
    """Simulates various fault scenarios using Docker commands."""

    def __init__(self, project_name: str = "faultsim"):
        """
        Initialize fault simulator.

        Args:
            project_name: Docker Compose project name
        """
        self.project_name = project_name
        self.active_fault: Optional[FaultScenario] = None

    def simulate_fault(self, scenario: FaultScenario, wait: bool = False) -> bool:
        """
        Simulate a fault scenario.

        Args:
            scenario: Fault scenario to simulate
            wait: Wait for fault simulation to complete

        Returns:
            True if fault simulation started successfully
        """
        logger.info(
            f"Simulating fault: {scenario.fault_type.value} "
            f"on {scenario.target_service} for {scenario.duration_minutes} minutes"
        )

        self.active_fault = scenario

        if scenario.fault_type == FaultType.REDIS_UNAVAILABLE:
            return self._simulate_redis_unavailable(scenario, wait)
        elif scenario.fault_type == FaultType.SERVICE_CRASH:
            return self._simulate_service_crash(scenario, wait)
        elif scenario.fault_type == FaultType.NETWORK_DELAY:
            return self._simulate_network_delay(scenario, wait)
        elif scenario.fault_type == FaultType.CPU_STRESS:
            return self._simulate_cpu_stress(scenario, wait)
        else:
            logger.error(f"Unsupported fault type: {scenario.fault_type}")
            return False

    def _simulate_redis_unavailable(self, scenario: FaultScenario, wait: bool) -> bool:
        """Simulate Redis becoming unavailable by stopping the container."""
        container_name = f"{self.project_name}_{scenario.target_service}_1"

        # Try alternative naming convention
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
        )
        containers = result.stdout.strip().split("\n")
        matching = [c for c in containers if scenario.target_service in c and self.project_name in c]

        if matching:
            container_name = matching[0]

        logger.info(f"Stopping container: {container_name}")

        try:
            # Stop the container
            subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if wait:
                # Wait for the duration
                time.sleep(scenario.duration_minutes * 60)

                # Restart the container
                logger.info(f"Restarting container: {container_name}")
                subprocess.run(
                    ["docker", "start", container_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            else:
                logger.info(f"Container stopped. Will auto-restart after {scenario.duration_minutes} minutes")

            return True
        except Exception as e:
            logger.error(f"Error simulating fault: {e}")
            return False

    def _simulate_service_crash(self, scenario: FaultScenario, wait: bool) -> bool:
        """Simulate service crash by killing the main process."""
        container_name = f"{self.project_name}_{scenario.target_service}_1"

        try:
            # Send SIGKILL to main process
            subprocess.run(
                ["docker", "exec", container_name, "kill", "-9", "1"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if wait:
                time.sleep(scenario.duration_minutes * 60)

            return True
        except Exception as e:
            logger.error(f"Error simulating service crash: {e}")
            return False

    def _simulate_network_delay(self, scenario: FaultScenario, wait: bool) -> bool:
        """Simulate network delay using tc (traffic control)."""
        container_name = f"{self.project_name}_{scenario.target_service}_1"
        delay_ms = scenario.params.get("delay_ms", 1000) if scenario.params else 1000

        try:
            # Add network delay
            subprocess.run(
                [
                    "docker", "exec", container_name,
                    "tc", "qdisc", "add", "dev", "eth0", "root", "netem",
                    "delay", f"{delay_ms}ms",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if wait:
                time.sleep(scenario.duration_minutes * 60)

                # Remove network delay
                subprocess.run(
                    ["docker", "exec", container_name, "tc", "qdisc", "del", "dev", "eth0", "root"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

            return True
        except Exception as e:
            logger.error(f"Error simulating network delay: {e}")
            return False

    def _simulate_cpu_stress(self, scenario: FaultScenario, wait: bool) -> bool:
        """Simulate CPU stress using stress-ng."""
        container_name = f"{self.project_name}_{scenario.target_service}_1"
        cpu_load = scenario.params.get("cpu_load", 2) if scenario.params else 2

        try:
            # Start CPU stress
            cmd = [
                "docker", "exec", "-d", container_name,
                "stress-ng", "--cpu", str(cpu_load),
                "--timeout", f"{scenario.duration_minutes}m",
            ]
            subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if wait:
                time.sleep(scenario.duration_minutes * 60)

            return True
        except Exception as e:
            logger.error(f"Error simulating CPU stress: {e}")
            return False

    def stop_fault(self) -> bool:
        """
        Stop the active fault simulation.

        Returns:
            True if fault stopped successfully
        """
        if not self.active_fault:
            logger.warning("No active fault to stop")
            return False

        logger.info(f"Stopping fault simulation: {self.active_fault.fault_type.value}")

        # For now, just log - specific cleanup depends on fault type
        # In production, implement proper cleanup for each fault type
        self.active_fault = None
        return True
