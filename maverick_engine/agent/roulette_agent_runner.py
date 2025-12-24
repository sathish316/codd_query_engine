import logging
import os

from opus_agent_base.agent.agent_runner import AgentRunner
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager
from maverick_engine.custom_tool.roulette_wheel_tool import RouletteWheelTool
from maverick_engine.agent.roulette_agent_builder import RouletteAgentBuilder
from maverick_engine.utils.file_utils import expand_path

logger = logging.getLogger(__name__)


async def run_roulette_agent():
    """Run Roulette Agent using AgentRunner"""
    logger.info("🎯 Starting Roulette Agent")

    # Build Roulette Agent
    maverick_home = expand_path("$HOME/.maverick")
    config_manager = ConfigManager(maverick_home, "config.yml")
    instructions_manager = InstructionsManager()
    roulette_agent = (
        RouletteAgentBuilder(config_manager)
        .name("roulette-agent")
        .set_system_prompt_keys(["roulette_agent_instruction"])
        .add_instructions_manager(instructions_manager)
        .add_model_manager()
        .instruction(
            "roulette_agent_instruction",
            expand_path("$HOME/.maverick/prompts/agent/ROULETTE_AGENT_INSTRUCTIONS.md")
        )
        .custom_tool(RouletteWheelTool())
        .build()
    )
    # Run Roulette Agent
    agent_runner = AgentRunner(roulette_agent)
    await agent_runner.run_agent()

def main():
    import asyncio
    asyncio.run(run_roulette_agent())

if __name__ == "__main__":
    main()
