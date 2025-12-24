import logging

from opus_agent_base.agent.agent_runner import AgentRunner
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager
from maverick_engine.custom_tool.roulette_wheel_tool import RouletteWheelTool
from maverick_engine.agent.roulette_agent_builder import RouletteAgentBuilder

logger = logging.getLogger(__name__)


async def run_roulette_agent():
    """Run Roulette Agent using AgentRunner"""
    logger.info("🎯 Starting Roulette Agent")

    # Build DeepWork Agent
    config_manager = ConfigManager("~/.maverick/config.yml")
    instructions_manager = InstructionsManager()
    roulette_agent = (
        RouletteAgentBuilder(config_manager)
        .name("roulette-agent")
        .set_system_prompt_keys(["roulette_agent_instruction"])
        .add_instructions_manager(instructions_manager)
        .add_model_manager()
        .instruction(
            "roulette_agent_instruction", "~/.maverick/prompts/agent/ROULETTE_AGENT_INSTRUCTIONS.md"
        )
        .custom_tool(RouletteWheelTool())
        .build()
    )
    # Run Roulette Agent
    agent_runner = AgentRunner(roulette_agent)
    await agent_runner.run_agent()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_roulette_agent())
