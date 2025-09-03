"""EvoSuite Core Runtime."""

__version__ = "0.2.0"

# Core imports for public API
from .agent_os.config import load_agent_os_config
from .agent_os.coordinator import AgentCoordinator

__all__ = [
    "load_agent_os_config",
    "AgentCoordinator",
]