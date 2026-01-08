# Fault Simulation Suite

A minimal Golang framework for running fault simulation scenarios with AI-powered root cause investigation.

## Overview

This framework executes YAML-defined fault simulation scenarios through a series of steps:
1. **Setup Service** - Start and wait for services (blocking)
2. **Steady Traffic** - Generate baseline load (non-blocking)
3. **Fault Stimulation** - Inject faults (non-blocking)
4. **Investigation** - AI-powered root cause analysis using Claude (blocking)
5. **User Feedback** - Validate results with user input (blocking)

## Architecture

```
faultsim/
├── cmd/          # CLI application
├── pkg/          # Core framework (types, executor, loader)
├── scenarios/    # YAML scenario definitions
└── scripts/      # Shell scripts for setup, traffic, and fault injection
```

## Installation

```bash
cd faultsim
go mod download
go build -o faultsim cmd/main.go
```

## Usage

### Run a Single Scenario

```bash
./faultsim -scenario scenarios/beer-redis-failure.yml
```

### Run All Scenarios

```bash
./faultsim -scenario 'scenarios/*.yml'
```

## Creating a Scenario

Create a YAML file in `scenarios/` with the following structure:

```yaml
service_name: my-service
service_path: path/to/service
scenario_name: my-scenario
scenario_description: Description of what this scenario tests

steps:
  - name: Setup Service
    description: Start the service
    type: setup_service
    params:
      script_path: scripts/setup.sh
      timeout: 300

  - name: Generate Traffic
    description: Send requests to service
    type: steady_traffic
    params:
      script_path: scripts/traffic.sh
      script_args:
        - "http://localhost:8080"
        - "10"

  - name: Inject Fault
    description: Simulate a failure
    type: fault_stimulation
    params:
      script_path: scripts/inject-fault.sh
      delay: 30

  - name: Investigate
    description: Find root cause with AI
    type: investigation
    params:
      timeout: 600
      prompt: |
        Investigate the root cause of issues in my-service.
        Use Prometheus and Loki to analyze the problem.

  - name: Validate
    description: Confirm root cause matches expected fault
    type: user_feedback
    params:
      expected_fault: Redis connection failure
      question: Does the investigation identify Redis as the problem?
```

## Step Types

### 1. setup_service (Blocking)
Runs a setup script and waits for completion.

**Required params:**
- `script_path`: Path to setup script
- `timeout`: Maximum seconds to wait (default: 300)

### 2. steady_traffic (Non-blocking)
Starts a traffic generation script in the background.

**Required params:**
- `script_path`: Path to traffic script

**Optional params:**
- `script_args`: Array of arguments to pass to script

### 3. fault_stimulation (Non-blocking)
Injects a fault by running a script in the background.

**Required params:**
- `script_path`: Path to fault injection script

**Optional params:**
- `delay`: Seconds to wait before injecting fault (default: 0)
- `script_args`: Array of arguments to pass to script

### 4. investigation (Blocking)
Runs Claude CLI with a prompt to investigate the root cause.

**Required params:**
- `prompt`: Investigation prompt for Claude

**Optional params:**
- `timeout`: Maximum seconds to wait (default: 600)

### 5. user_feedback (Blocking)
Asks the user to confirm if the investigation matches the expected fault.

**Required params:**
- `expected_fault`: Description of the fault that was injected
- `question`: Question to ask the user (Y/N)

## Example Scenario: Beer Service Redis Failure

The included example (`scenarios/beer-redis-failure.yml`) demonstrates:
1. Starting beer service with Docker Compose
2. Generating HTTP traffic
3. Stopping Redis to simulate cache failure
4. Using Claude to investigate metrics and logs
5. User validation of root cause analysis

Run it with:
```bash
./faultsim -scenario scenarios/beer-redis-failure.yml
```

## Using Existing Beer Service Scripts

The framework is designed to reuse existing scripts from `sandbox/beer-service-sandbox`:

### Traffic Generation Scripts
Use existing traffic generation scripts from the beer-service sandbox. Reference them in scenario YAML:
```yaml
params:
  script_path: ../sandbox/beer-service-sandbox/scripts/generate-traffic.sh
  script_args: ["http://localhost:5001", "10"]
```

### Chaos/Fault Injection Scripts
Use existing chaos generation scripts from the beer-service sandbox. For each chaos script, create a corresponding scenario YAML file.

**Example**: If `sandbox/beer-service-sandbox/chaos/redis-down.sh` exists, create `scenarios/beer-redis-down.yml` that references it.

### Parameterizing Scripts
If existing scripts need modification for the framework, parameterize them to accept:
- Service URLs
- Duration/timeout values
- Resource limits
- Fault intensity

## Configuration

The framework uses Maverick's existing config for service endpoints:
- Prometheus: From Maverick config at `~/.maverick/config.yml`
- Loki: From Maverick config
- Redis: From Maverick config
- Service endpoints: Defined in scenario YAML

Optional fault simulation config: `~/.maverick_faultsim_evals/config.yml`

## Writing Shell Scripts

Scripts should:
- Use `#!/bin/bash` shebang
- Exit with code 0 on success, non-zero on failure
- Print useful status messages
- For non-blocking scripts: Run indefinitely until killed

## Extending the Framework

To add new step types:
1. Add constant in `pkg/types.go`
2. Add case in `pkg/executor.go::executeStep()`
3. Implement execution logic
4. Update this README

## Troubleshooting

**Scripts not executing:**
- Ensure scripts are executable: `chmod +x scripts/*.sh`
- Check script paths are relative to where you run `faultsim`

**Investigation timing out:**
- Increase `timeout` in investigation step params
- Simplify investigation prompt

**Services not starting:**
- Verify Docker/Docker Compose are running
- Check service paths in scenario YAML
- Review setup script output
