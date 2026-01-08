package pkg

import (
	"fmt"
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

// LoadScenario loads a scenario from a YAML file
func LoadScenario(path string) (*Scenario, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read scenario file: %w", err)
	}

	var scenario Scenario
	if err := yaml.Unmarshal(data, &scenario); err != nil {
		return nil, fmt.Errorf("failed to parse scenario YAML: %w", err)
	}

	return &scenario, nil
}

// LoadScenarios loads multiple scenarios matching a glob pattern
func LoadScenarios(pattern string) ([]*Scenario, error) {
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return nil, fmt.Errorf("failed to match pattern: %w", err)
	}

	if len(matches) == 0 {
		return nil, fmt.Errorf("no scenarios found matching pattern: %s", pattern)
	}

	scenarios := make([]*Scenario, 0, len(matches))
	for _, match := range matches {
		scenario, err := LoadScenario(match)
		if err != nil {
			return nil, fmt.Errorf("failed to load %s: %w", match, err)
		}
		scenarios = append(scenarios, scenario)
	}

	return scenarios, nil
}
