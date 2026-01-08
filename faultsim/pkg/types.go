package pkg

// Scenario represents a fault simulation test scenario
type Scenario struct {
	ServiceName        string `yaml:"service_name"`
	ServicePath        string `yaml:"service_path"`
	ScenarioName       string `yaml:"scenario_name"`
	ScenarioDescription string `yaml:"scenario_description"`
	Steps              []Step `yaml:"steps"`
}

// Step represents a single step in a fault simulation scenario
type Step struct {
	Name        string                 `yaml:"name"`
	Description string                 `yaml:"description"`
	Type        string                 `yaml:"type"`
	Params      map[string]interface{} `yaml:"params"`
}

// StepType constants
const (
	StepTypeSetupService     = "setup_service"
	StepTypeSteadyTraffic    = "steady_traffic"
	StepTypeFaultStimulation = "fault_stimulation"
	StepTypeInvestigation    = "investigation"
	StepTypeUserFeedback     = "user_feedback"
)
