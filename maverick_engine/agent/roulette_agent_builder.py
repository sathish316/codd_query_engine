from opus_agent_base.agent.agent_builder import AgentBuilder
from opus_agent_base.config.config_manager import ConfigManager


class RouletteAgentBuilder(AgentBuilder):
    """Builder for Roulette Agent"""

    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)

    def build(self) -> AgentBuilder:
        """Build the DeepWork agent with all components"""
        # self._add_mcp_servers_config()
        return self

    def _add_mcp_servers_config(self):
        """Add MCP servers"""
        # mcp_server_registry = MCPServerRegistry()
        # deepwork_mcp_server_registry = DeepWorkMCPServerRegistry(self.config_manager)
        # mcp_servers_config = [
        #     mcp_server_registry.get_datetime_mcp_server(),
        #     deepwork_mcp_server_registry.get_clockwise_fastmcp_server(),
        # ]
        # self.add_mcp_servers_config(mcp_servers_config)

# from pydantic_ai import Agent, RunContext

# roulette_agent = Agent(  
#     'openai:gpt-5',
#     deps_type=int,
#     output_type=bool,
#     system_prompt=(
#         'Use the `roulette_wheel` function to see if the '
#         'customer has won based on the number they provide.'
#     ),
# )




# # Run the agent
# success_number = 18  
# result = roulette_agent.run_sync('Put my money on square eighteen', deps=success_number)
# print(result.output)  
# #> True

# result = roulette_agent.run_sync('I bet five is the winner', deps=success_number)
# print(result.output)
# #> False