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
