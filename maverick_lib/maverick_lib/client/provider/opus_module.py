"""Dependency injection module for Opus Agent operations (Spring-like pattern)."""

from pathlib import Path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

from maverick_lib.config import MaverickConfig


class OpusModule:
    """Module for Opus Agent operations - provides configured dependencies."""

    @classmethod
    def get_config_manager(cls, config: MaverickConfig) -> ConfigManager:
        """
        Provide a configured ConfigManager instance.

        Args:
            config: MaverickConfig with config path

        Returns:
            ConfigManager instance
        """
        # Extract directory from config_path (it may include config.yml)
        config_path = Path(config.config_path).expanduser()
        config_dir = config_path.parent
        config_file = config_path.name

        return ConfigManager(str(config_dir), config_file)

    @classmethod
    def get_instructions_manager(cls) -> InstructionsManager:
        """
        Provide an InstructionsManager instance.

        Returns:
            InstructionsManager instance
        """
        return InstructionsManager()
