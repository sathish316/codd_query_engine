package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/sathish316/maverickv2/faultsim/pkg"
)

func main() {
	scenarioPath := flag.String("scenario", "", "Path to scenario YAML file or glob pattern (e.g., scenarios/*.yml)")
	flag.Parse()

	if *scenarioPath == "" {
		fmt.Println("Error: -scenario flag is required")
		fmt.Println("\nUsage:")
		fmt.Println("  Run single scenario: faultsim -scenario scenarios/beer-redis-failure.yml")
		fmt.Println("  Run all scenarios:   faultsim -scenario 'scenarios/*.yml'")
		os.Exit(1)
	}

	// Check if pattern contains wildcards
	if hasWildcard(*scenarioPath) {
		runMultipleScenarios(*scenarioPath)
	} else {
		runSingleScenario(*scenarioPath)
	}
}

func runSingleScenario(path string) {
	scenario, err := pkg.LoadScenario(path)
	if err != nil {
		fmt.Printf("Error loading scenario: %v\n", err)
		os.Exit(1)
	}

	executor := pkg.NewExecutor(scenario)
	if err := executor.Execute(); err != nil {
		fmt.Printf("\n❌ Scenario failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("✅ Scenario completed successfully")
}

func runMultipleScenarios(pattern string) {
	scenarios, err := pkg.LoadScenarios(pattern)
	if err != nil {
		fmt.Printf("Error loading scenarios: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("\n=== Running %d scenarios ===\n\n", len(scenarios))

	passed := 0
	failed := 0

	for i, scenario := range scenarios {
		fmt.Printf("[%d/%d] ", i+1, len(scenarios))

		executor := pkg.NewExecutor(scenario)
		if err := executor.Execute(); err != nil {
			fmt.Printf("❌ Failed: %v\n\n", err)
			failed++
		} else {
			fmt.Printf("✅ Passed\n\n")
			passed++
		}
	}

	fmt.Printf("\n=== Summary ===\n")
	fmt.Printf("Total: %d | Passed: %d | Failed: %d\n", len(scenarios), passed, failed)

	if failed > 0 {
		os.Exit(1)
	}
}

func hasWildcard(path string) bool {
	for _, char := range path {
		if char == '*' || char == '?' || char == '[' {
			return true
		}
	}
	return false
}
