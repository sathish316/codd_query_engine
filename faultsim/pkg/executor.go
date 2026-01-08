package pkg

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

// Executor handles execution of scenario steps
type Executor struct {
	scenario *Scenario
}

// NewExecutor creates a new step executor
func NewExecutor(scenario *Scenario) *Executor {
	return &Executor{scenario: scenario}
}

// Execute runs all steps in the scenario
func (e *Executor) Execute() error {
	fmt.Printf("\n=== Starting Scenario: %s ===\n", e.scenario.ScenarioName)
	fmt.Printf("Service: %s\n", e.scenario.ServiceName)
	fmt.Printf("Description: %s\n\n", e.scenario.ScenarioDescription)

	for i, step := range e.scenario.Steps {
		fmt.Printf("[Step %d/%d] %s\n", i+1, len(e.scenario.Steps), step.Name)
		fmt.Printf("  Description: %s\n", step.Description)
		fmt.Printf("  Type: %s\n", step.Type)

		if err := e.executeStep(step); err != nil {
			return fmt.Errorf("step %d failed: %w", i+1, err)
		}
		fmt.Println()
	}

	fmt.Printf("=== Scenario Completed: %s ===\n\n", e.scenario.ScenarioName)
	return nil
}

// executeStep executes a single step based on its type
func (e *Executor) executeStep(step Step) error {
	switch step.Type {
	case StepTypeSetupService:
		return e.executeSetupService(step)
	case StepTypeSteadyTraffic:
		return e.executeSteadyTraffic(step)
	case StepTypeFaultStimulation:
		return e.executeFaultStimulation(step)
	case StepTypeInvestigation:
		return e.executeInvestigation(step)
	case StepTypeUserFeedback:
		return e.executeUserFeedback(step)
	default:
		return fmt.Errorf("unknown step type: %s", step.Type)
	}
}

// executeSetupService runs setup script in blocking mode
func (e *Executor) executeSetupService(step Step) error {
	scriptPath := getStringParam(step.Params, "script_path")
	timeout := getIntParam(step.Params, "timeout", 300)

	fmt.Printf("  Executing setup script (blocking, timeout=%ds): %s\n", timeout, scriptPath)

	return e.runScript(scriptPath, timeout, true, step.Params)
}

// executeSteadyTraffic runs traffic script in non-blocking mode
func (e *Executor) executeSteadyTraffic(step Step) error {
	scriptPath := getStringParam(step.Params, "script_path")

	fmt.Printf("  Starting traffic script (non-blocking): %s\n", scriptPath)

	return e.runScript(scriptPath, 0, false, step.Params)
}

// executeFaultStimulation runs fault script in non-blocking mode
func (e *Executor) executeFaultStimulation(step Step) error {
	scriptPath := getStringParam(step.Params, "script_path")
	delay := getIntParam(step.Params, "delay", 0)

	if delay > 0 {
		fmt.Printf("  Waiting %d seconds before fault injection...\n", delay)
		time.Sleep(time.Duration(delay) * time.Second)
	}

	fmt.Printf("  Injecting fault (non-blocking): %s\n", scriptPath)

	return e.runScript(scriptPath, 0, false, step.Params)
}

// executeInvestigation runs Claude investigation in blocking mode
func (e *Executor) executeInvestigation(step Step) error {
	prompt := getStringParam(step.Params, "prompt")
	timeout := getIntParam(step.Params, "timeout", 600)

	fmt.Printf("  Running AI investigation (blocking, timeout=%ds)...\n", timeout)

	cmd := exec.Command("claude", "-p", prompt)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	done := make(chan error, 1)
	go func() {
		done <- cmd.Run()
	}()

	select {
	case err := <-done:
		return err
	case <-time.After(time.Duration(timeout) * time.Second):
		cmd.Process.Kill()
		return fmt.Errorf("investigation timed out after %d seconds", timeout)
	}
}

// executeUserFeedback asks user for feedback
func (e *Executor) executeUserFeedback(step Step) error {
	question := getStringParam(step.Params, "question")
	expectedFault := getStringParam(step.Params, "expected_fault")

	fmt.Printf("\n  Expected Fault: %s\n", expectedFault)
	fmt.Printf("  %s (Y/N): ", question)

	reader := bufio.NewReader(os.Stdin)
	response, err := reader.ReadString('\n')
	if err != nil {
		return fmt.Errorf("failed to read user input: %w", err)
	}

	response = strings.TrimSpace(strings.ToUpper(response))

	if response == "Y" || response == "YES" {
		fmt.Printf("  ✓ Test PASSED\n")
		return nil
	} else if response == "N" || response == "NO" {
		return fmt.Errorf("test FAILED: user indicated root cause does not match")
	} else {
		return fmt.Errorf("invalid response: expected Y or N, got %s", response)
	}
}

// runScript executes a shell script with optional blocking and timeout
func (e *Executor) runScript(scriptPath string, timeout int, blocking bool, params map[string]interface{}) error {
	if scriptPath == "" {
		return fmt.Errorf("script_path is required")
	}

	// Build command with additional parameters
	args := []string{scriptPath}

	// Add additional script arguments from params
	if scriptArgs, ok := params["script_args"].([]interface{}); ok {
		for _, arg := range scriptArgs {
			args = append(args, fmt.Sprintf("%v", arg))
		}
	}

	cmd := exec.Command("/bin/bash", args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if blocking {
		// Run in blocking mode with timeout
		done := make(chan error, 1)
		go func() {
			done <- cmd.Run()
		}()

		if timeout > 0 {
			select {
			case err := <-done:
				return err
			case <-time.After(time.Duration(timeout) * time.Second):
				cmd.Process.Kill()
				return fmt.Errorf("script timed out after %d seconds", timeout)
			}
		} else {
			return <-done
		}
	} else {
		// Run in non-blocking mode
		if err := cmd.Start(); err != nil {
			return fmt.Errorf("failed to start script: %w", err)
		}
		fmt.Printf("  Script started with PID: %d\n", cmd.Process.Pid)
		return nil
	}
}

// Helper functions to extract parameters
func getStringParam(params map[string]interface{}, key string) string {
	if val, ok := params[key]; ok {
		return fmt.Sprintf("%v", val)
	}
	return ""
}

func getIntParam(params map[string]interface{}, key string, defaultVal int) int {
	if val, ok := params[key]; ok {
		switch v := val.(type) {
		case int:
			return v
		case float64:
			return int(v)
		}
	}
	return defaultVal
}
