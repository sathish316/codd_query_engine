from opus_agent_base.tools.custom_tool import CustomTool
from pydantic_ai import RunContext


class RouletteWheelTool(CustomTool):
    """
    Tool for the roulette wheel
    """

    def __init__(
        self, config_manager=None, instructions_manager=None, model_manager=None
    ):
        super().__init__(
            "roulette_wheel",
            "roulette.wheel",
            config_manager,
            instructions_manager,
            model_manager,
        )

    def initialize_tools(self, agent):
        @agent.tool
        def roulette_wheel(ctx: RunContext[int], square: int) -> str:
            """
            Check if the square is a winner
            """
            return "winner" if square == 5 else "loser"
