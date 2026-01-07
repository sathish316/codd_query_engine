# Fault Simulation Integration Tests

This directory contains reusable components and tests for fault simulation and AI-powered root cause investigation.

## Overview

The fault simulation framework allows you to:
1. Start services in Docker Compose
2. Generate realistic traffic
3. Inject various fault scenarios (Redis unavailable, network delays, etc.)
4. Validate fault presence
5. Run AI-powered investigations using Claude or Codex
6. Validate the investigation correctly identified the root cause

## Architecture

The framework is designed with **reusable modules** to make it easy to create new fault simulation tests:

```
faultsim/
├── utils/                          # Reusable utility modules
│   ├── docker_manager.py          # Docker Compose management
│   ├── traffic_generator.py       # HTTP traffic generation
│   ├── fault_simulator.py         # Fault injection scenarios
│   └── health_checker.py          # Service health and fault validation
├── skills/                         # Investigation skills/prompts
│   └── investigate_root_cause.md  # Root cause investigation skill
├── config.yml                      # Test configuration
├── docker-compose.faultsim.yml    # Docker Compose setup
└── test_redis_unavailable_investigation.py  # Example test

```

## Prerequisites

1. **Beer Service Sandbox**: Initialize the submodule
   ```bash
   git submodule update --init --recursive
   ```

2. **Docker and Docker Compose**: Ensure both are installed and running

3. **Python Dependencies**: Install test dependencies
   ```bash
   uv sync --dev
   ```

4. **Claude or Codex**: Configure one of:
   - `claude` CLI (Claude Code)
   - `codex` CLI

## Configuration

Edit `config.yml` to customize:

```yaml
# Traffic generation
traffic:
  duration_minutes: 1  # How long to generate traffic
  requests_per_second: 10

# Fault simulation
fault:
  type: redis_unavailable  # Fault type
  target_service: redis-cache
  duration_minutes: 5

# Investigation
investigation:
  executor: claude  # 'claude' or 'codex'
  timeout_minutes: 10
```

### Supported Fault Types

- `redis_unavailable`: Stops Redis container to simulate cache unavailability
- `service_crash`: Kills the main service process
- `network_delay`: Adds network latency using tc (traffic control)
- `cpu_stress`: Stresses CPU using stress-ng

## Running Tests

### Run the Example Test

```bash
# Run with pytest
uv run pytest -m integration_faultsim_evals -s -v

# Run specific test
uv run pytest tests/integration/faultsim/test_redis_unavailable_investigation.py -s -v
```

### Run Without Integration Tag

By default, integration tests are excluded:
```bash
uv run pytest  # Won't run these tests
```

## Creating New Fault Simulation Tests

The framework is designed for reusability. Here's how to create a new test:

### 1. Create a New Test File

```python
import pytest
from utils import (
    DockerManager,
    TrafficGenerator,
    TrafficConfig,
    FaultSimulator,
    FaultScenario,
    FaultType,
    HealthChecker,
)

@pytest.mark.integration
@pytest.mark.integration_faultsim_evals
class TestMyNewFaultScenario:
    def test_network_delay_investigation(self, test_config, docker_manager):
        # 1. Start services
        docker_manager.start_services()

        # 2. Generate traffic
        traffic_gen = TrafficGenerator(TrafficConfig(...))
        traffic_gen.start(background=True)

        # 3. Inject fault
        fault_sim = FaultSimulator(project_name="faultsim")
        scenario = FaultScenario(
            fault_type=FaultType.NETWORK_DELAY,
            target_service="beer-service",
            duration_minutes=5,
            params={"delay_ms": 2000}
        )
        fault_sim.simulate_fault(scenario, wait=False)

        # 4. Run investigation
        # ... investigation logic ...

        # 5. Validate results
        # ... validation logic ...
```

### 2. Create a Custom Investigation Skill

Create a new markdown file in `skills/`:

```markdown
# My Custom Investigation Skill

You are investigating a specific type of failure...

## Investigation Steps
1. ...
2. ...

## Output Format
Write your findings to `/tmp/my_investigation_result.json`
```

### 3. Update Configuration

Create a custom config or extend `config.yml`:

```yaml
fault:
  type: network_delay
  target_service: beer-service
  duration_minutes: 3
  params:
    delay_ms: 2000
```

## Reusable Modules

### DockerManager

Manages Docker Compose lifecycle:

```python
from utils import DockerManager

docker = DockerManager(compose_file="docker-compose.yml", project_name="test")

# Start all services
docker.start_services()

# Start specific services
docker.start_services(services=["beer-service", "redis-cache"])

# Wait for healthy
docker.wait_for_healthy("beer-service", timeout=120)

# Get logs
logs = docker.get_logs("beer-service", tail=100)

# Cleanup
docker.cleanup(volumes=True)
```

### TrafficGenerator

Generates HTTP traffic:

```python
from utils import TrafficGenerator, TrafficConfig

config = TrafficConfig(
    url="http://localhost:5001",
    duration_minutes=2,
    requests_per_second=20,
    endpoints=["/beers", "/health"]
)

traffic = TrafficGenerator(config)
traffic.start(background=True)  # Run in background

# Get statistics
stats = traffic.get_stats()
# {"total_requests": 2400, "errors": 12, "success_rate": 99.5}

traffic.stop()
```

### FaultSimulator

Injects fault scenarios:

```python
from utils import FaultSimulator, FaultScenario, FaultType

fault_sim = FaultSimulator(project_name="faultsim")

# Redis unavailable
scenario = FaultScenario(
    fault_type=FaultType.REDIS_UNAVAILABLE,
    target_service="redis-cache",
    duration_minutes=5
)
fault_sim.simulate_fault(scenario, wait=False)

# Network delay
scenario = FaultScenario(
    fault_type=FaultType.NETWORK_DELAY,
    target_service="beer-service",
    duration_minutes=3,
    params={"delay_ms": 1000}
)
fault_sim.simulate_fault(scenario, wait=True)
```

### HealthChecker

Validates service health and fault presence:

```python
from utils import HealthChecker

health = HealthChecker(base_url="http://localhost:5001")

# Check health
is_healthy = health.check_health(endpoint="/health")

# Check readiness (returns dict with details)
readiness = health.check_readiness(endpoint="/ready")

# Validate fault is present
fault_detected = health.validate_fault_present(
    fault_type="redis_unavailable",
    endpoint="/ready"
)
```

## Investigation Output

The AI investigation produces a JSON file with this structure:

```json
{
  "root_cause": "Redis cache became unavailable",
  "affected_component": "Redis",
  "evidence": [
    "beer_redis_errors_total metric spiked at 15:23:00",
    "Logs show 'connection refused' errors to Redis"
  ],
  "timeline": "2025-01-07 15:23:00 UTC",
  "confidence": "high",
  "recommendations": [
    "Restart Redis service",
    "Implement Redis connection retry logic with exponential backoff"
  ]
}
```

## Validation

The test validates:
1. **Fault injection**: Fault was successfully injected
2. **Fault detection**: Fault is observable in the system
3. **Investigation accuracy**: Root cause matches expected fault
4. **Confidence level**: Investigation has appropriate confidence

Similarity threshold (default 0.7) determines how closely the investigation must match expected keywords.

## Tips

1. **Don't wait for fault simulation**: Use `wait=False` to continue test while fault runs
2. **Preserve output**: Output files are not cleaned up for inspection
3. **Adjust timeouts**: Increase investigation timeout for complex scenarios
4. **Check logs**: Use `docker_manager.get_logs()` for debugging
5. **Reuse components**: All modules are designed to be reusable

## Extending the Framework

To add a new fault type:

1. Add enum to `FaultType` in `fault_simulator.py`
2. Implement `_simulate_<fault_type>()` method
3. Add validation logic to `health_checker.py`
4. Update `config.yml` with new fault parameters

## Troubleshooting

**Services won't start**:
- Check `docker ps` for port conflicts
- Verify beer-service-sandbox submodule is initialized
- Check Docker daemon is running

**Investigation times out**:
- Increase `investigation.timeout_minutes` in config
- Check MCP servers are accessible
- Verify Prometheus/Loki have data

**Fault not detected**:
- Increase wait time after fault injection
- Check fault actually affected the service
- Verify validation logic in `health_checker.py`

**Root cause validation fails**:
- Review investigation output in `/tmp/faultsim_root_cause.json`
- Adjust `validation.similarity_threshold` in config
- Update `expected_root_cause_keywords` for your fault type
