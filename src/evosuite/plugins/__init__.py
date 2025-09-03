"""Plugin system base classes and interfaces."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class PluginMetadata(BaseModel):
    """Metadata for plugin registration."""
    name: str
    version: str
    description: str
    author: str
    provides: List[str]  # capability IDs
    requires_core: str  # semver range
    config_schema: Optional[Dict[str, Any]] = None


class Plugin(ABC):
    """Base class for all EvoSuite plugins."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._metadata: Optional[PluginMetadata] = None
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    async def activate(self, context: Dict[str, Any]) -> None:
        """Called when plugin is activated."""
        pass
    
    async def deactivate(self, context: Dict[str, Any]) -> None:
        """Called when plugin is deactivated."""
        pass


class Evaluator(Plugin):
    """Base class for evaluation plugins."""
    
    @abstractmethod
    async def evaluate(self, candidate: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a candidate solution."""
        pass


class Mutator(Plugin):
    """Base class for mutation plugins."""
    
    @abstractmethod
    async def mutate(self, candidate: Any, context: Dict[str, Any]) -> Any:
        """Mutate a candidate solution."""
        pass


class SamplingStrategy(Plugin):
    """Base class for sampling strategy plugins."""
    
    @abstractmethod
    async def sample(self, population: List[Any], context: Dict[str, Any]) -> List[Any]:
        """Sample from population according to strategy."""
        pass


class Provider(Plugin):
    """Base class for LLM provider plugins."""
    
    @abstractmethod
    async def generate(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate response from LLM provider."""
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate provider configuration (API keys, etc.)."""
        pass


__all__ = [
    "Plugin",
    "PluginMetadata", 
    "Evaluator",
    "Mutator",
    "SamplingStrategy",
    "Provider"
]