"""
Fault simulation integration test for Redis unavailability investigation.

This test validates the complete fault simulation and investigation workflow:
1. Starts the beer service sandbox using Docker Compose
2. Generates traffic to establish baseline
3. Injects a Redis unavailability fault
4. Validates the fault is present
5. Runs an AI-powered root cause investigation
6. Validates the investigation correctly identified the root cause
"""

import os
import json
import time
import logging
import subprocess
from pathlib import Path
import pytest
import yaml
from difflib import SequenceMatcher

from utils import (
    DockerManager,
    TrafficGenerator,
    TrafficConfig,
    FaultSimulator,
    FaultScenario,
    FaultType,
    HealthChecker,
)

logger = logging.getLogger(__name__)

# Test configuration paths
TEST_DIR = Path(__file__).parent
CONFIG_FILE = TEST_DIR / "config.yml"


@pytest.fixture(scope="module")
def test_config():
    """Load test configuration from YAML file."""
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f)
    return config


@pytest.fixture(scope="module")
def docker_manager(test_config):
    """Create Docker manager for the test."""
    compose_file = TEST_DIR / test_config["docker"]["compose_file"]
    return DockerManager(
        compose_file=str(compose_file),
        project_name=test_config["docker"]["project_name"],
    )


@pytest.fixture(scope="module")
def health_checker(test_config):
    """Create health checker for the service."""
    return HealthChecker(test_config["service"]["base_url"])


@pytest.mark.integration
@pytest.mark.integration_faultsim_evals
class TestRedisFaultSimulationAndInvestigation:
    """
    Integration test for fault simulation and AI-powered investigation.

    This test demonstrates a complete fault injection and investigation workflow
    using reusable components.
    """

    def test_redis_unavailable_investigation_workflow(
        self, test_config, docker_manager, health_checker
    ):
        """
        Complete workflow: Start services -> Generate traffic -> Inject fault ->
        Validate fault -> Investigate -> Validate root cause.

        This is a comprehensive integration test that validates:
        - Service startup and health
        - Traffic generation
        - Fault injection
        - Fault validation
        - AI-powered root cause investigation
        - Investigation accuracy
        """
        # ========== STEP 1: Start Services ==========
        logger.info("=" * 80)
        logger.info("STEP 1: Starting Docker Compose services")
        logger.info("=" * 80)

        assert docker_manager.start_services(), "Failed to start Docker services"

        # Wait for services to become healthy
        service_name = test_config["service"]["name"]
        startup_timeout = test_config["docker"]["startup_timeout"]
        assert docker_manager.wait_for_healthy(
            service_name, timeout=startup_timeout
        ), f"{service_name} did not become healthy"

        # Verify service is responding
        assert health_checker.check_health(), "Service health check failed"

        logger.info("Services started successfully")
        time.sleep(5)  # Allow metrics to stabilize

        # ========== STEP 2: Generate Traffic ==========
        logger.info("=" * 80)
        logger.info("STEP 2: Generating baseline traffic")
        logger.info("=" * 80)

        traffic_config = TrafficConfig(
            url=test_config["service"]["base_url"],
            duration_minutes=test_config["traffic"]["duration_minutes"],
            requests_per_second=test_config["traffic"]["requests_per_second"],
            endpoints=test_config["traffic"]["endpoints"],
        )

        traffic_gen = TrafficGenerator(traffic_config)
        traffic_gen.start(background=True)

        # Let traffic run for the configured duration
        traffic_duration_seconds = test_config["traffic"]["duration_minutes"] * 60
        logger.info(f"Traffic will run for {traffic_duration_seconds} seconds")
        time.sleep(traffic_duration_seconds + 5)  # Add buffer

        stats = traffic_gen.get_stats()
        logger.info(f"Traffic generation stats: {stats}")

        # ========== STEP 3: Inject Fault ==========
        logger.info("=" * 80)
        logger.info("STEP 3: Injecting fault scenario")
        logger.info("=" * 80)

        fault_config = test_config["fault"]
        fault_scenario = FaultScenario(
            fault_type=FaultType(fault_config["type"]),
            target_service=fault_config["target_service"],
            duration_minutes=fault_config["duration_minutes"],
            params=fault_config.get("params"),
        )

        fault_sim = FaultSimulator(project_name=test_config["docker"]["project_name"])
        assert fault_sim.simulate_fault(
            fault_scenario, wait=False
        ), "Failed to inject fault"

        logger.info("Fault injected, waiting for propagation...")
        time.sleep(10)  # Allow fault to propagate

        # ========== STEP 4: Validate Fault is Present ==========
        logger.info("=" * 80)
        logger.info("STEP 4: Validating fault is present")
        logger.info("=" * 80)

        fault_present = health_checker.validate_fault_present(
            fault_type=fault_config["type"],
            endpoint=test_config["service"]["ready_endpoint"],
        )

        assert fault_present, "Fault was not detected in the system"
        logger.info("Fault presence validated")

        # ========== STEP 5: Run Investigation ==========
        logger.info("=" * 80)
        logger.info("STEP 5: Running AI-powered root cause investigation")
        logger.info("=" * 80)

        investigation_config = test_config["investigation"]
        skill_file = TEST_DIR / investigation_config["skill_file"]
        output_file = investigation_config["output_file"]

        # Clean up any previous output file
        if os.path.exists(output_file):
            os.remove(output_file)

        # Run investigation based on configured executor
        executor = investigation_config["executor"]
        if executor == "claude":
            investigation_success = self._run_claude_investigation(
                skill_file, output_file, investigation_config["timeout_minutes"]
            )
        elif executor == "codex":
            investigation_success = self._run_codex_investigation(
                skill_file, output_file, investigation_config["timeout_minutes"]
            )
        else:
            pytest.fail(f"Unknown investigation executor: {executor}")

        assert investigation_success, "Investigation failed to complete"
        logger.info("Investigation completed")

        # ========== STEP 6: Validate Root Cause ==========
        logger.info("=" * 80)
        logger.info("STEP 6: Validating root cause analysis")
        logger.info("=" * 80)

        # Read investigation output
        assert os.path.exists(output_file), f"Investigation output file not found: {output_file}"

        with open(output_file) as f:
            investigation_result = json.load(f)

        logger.info(f"Investigation result: {json.dumps(investigation_result, indent=2)}")

        # Validate root cause matches expected fault
        root_cause = investigation_result.get("root_cause", "").lower()
        affected_component = investigation_result.get("affected_component", "").lower()

        # Check for expected keywords
        expected_keywords = test_config["validation"]["expected_root_cause_keywords"]
        keyword_matches = sum(
            1 for keyword in expected_keywords
            if keyword in root_cause or keyword in affected_component
        )

        similarity_threshold = test_config["validation"]["similarity_threshold"]
        similarity_ratio = keyword_matches / len(expected_keywords)

        logger.info(
            f"Root cause similarity: {similarity_ratio:.2f} "
            f"(threshold: {similarity_threshold})"
        )

        assert similarity_ratio >= similarity_threshold, (
            f"Root cause analysis did not match expected fault. "
            f"Expected keywords: {expected_keywords}, "
            f"Got root_cause: {root_cause}, "
            f"affected_component: {affected_component}"
        )

        # Validate confidence level
        confidence = investigation_result.get("confidence", "low")
        assert confidence in ["high", "medium", "low"], "Invalid confidence level"

        logger.info(
            f"Root cause validated successfully with {confidence} confidence"
        )

        # ========== Test Complete ==========
        logger.info("=" * 80)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        # Note: Cleanup is NOT performed - output file is preserved for inspection
        logger.info(f"Investigation output preserved at: {output_file}")

    def _run_claude_investigation(
        self, skill_file: Path, output_file: str, timeout_minutes: int
    ) -> bool:
        """
        Run investigation using Claude via claude-code CLI.

        Args:
            skill_file: Path to investigation skill markdown
            output_file: Path where investigation should write results
            timeout_minutes: Maximum time for investigation

        Returns:
            True if investigation completed successfully
        """
        try:
            # Read skill content
            with open(skill_file) as f:
                skill_content = f.read()

            # Run claude with the skill as a prompt
            # Note: Adjust command based on your claude-code setup
            cmd = [
                "claude",
                "-p",
                skill_content,
            ]

            logger.info(f"Running investigation with command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_minutes * 60,
            )

            if result.returncode == 0:
                logger.info("Claude investigation completed")
                # Check if output file was created
                return os.path.exists(output_file)
            else:
                logger.error(f"Claude investigation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Investigation timed out")
            return False
        except Exception as e:
            logger.error(f"Error running investigation: {e}")
            return False

    def _run_codex_investigation(
        self, skill_file: Path, output_file: str, timeout_minutes: int
    ) -> bool:
        """
        Run investigation using codex exec.

        Args:
            skill_file: Path to investigation skill markdown
            output_file: Path where investigation should write results
            timeout_minutes: Maximum time for investigation

        Returns:
            True if investigation completed successfully
        """
        try:
            # Run codex exec with the skill file
            cmd = [
                "codex",
                "exec",
                "--skill",
                str(skill_file),
            ]

            logger.info(f"Running investigation with command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_minutes * 60,
            )

            if result.returncode == 0:
                logger.info("Codex investigation completed")
                return os.path.exists(output_file)
            else:
                logger.error(f"Codex investigation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Investigation timed out")
            return False
        except Exception as e:
            logger.error(f"Error running investigation: {e}")
            return False
