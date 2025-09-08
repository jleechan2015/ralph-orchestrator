# ABOUTME: Abstract base class for tool adapters
# ABOUTME: Defines the interface all tool adapters must implement

"""Base adapter interface for AI tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union
from pathlib import Path
import asyncio


@dataclass
class ToolResponse:
    """Response from a tool execution."""
    
    success: bool
    output: str
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ToolAdapter(ABC):
    """Abstract base class for tool adapters."""
    
    def __init__(self, name: str):
        self.name = name
        self.available = self.check_availability()
    
    @abstractmethod
    def check_availability(self) -> bool:
        """Check if the tool is available and properly configured."""
        pass
    
    @abstractmethod
    def execute(self, prompt: str, **kwargs) -> ToolResponse:
        """Execute the tool with the given prompt."""
        pass
    
    async def aexecute(self, prompt: str, **kwargs) -> ToolResponse:
        """Async execute the tool with the given prompt.
        
        Default implementation runs sync execute in thread pool.
        Subclasses can override for native async support.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, prompt, **kwargs)
    
    def execute_with_file(self, prompt_file: Path, **kwargs) -> ToolResponse:
        """Execute the tool with a prompt file."""
        if not prompt_file.exists():
            return ToolResponse(
                success=False,
                output="",
                error=f"Prompt file {prompt_file} not found"
            )
        
        with open(prompt_file, 'r') as f:
            prompt = f.read()
        
        return self.execute(prompt, **kwargs)
    
    async def aexecute_with_file(self, prompt_file: Path, **kwargs) -> ToolResponse:
        """Async execute the tool with a prompt file."""
        if not prompt_file.exists():
            return ToolResponse(
                success=False,
                output="",
                error=f"Prompt file {prompt_file} not found"
            )
        
        with open(prompt_file, 'r') as f:
            prompt = f.read()
        
        return await self.aexecute(prompt, **kwargs)
    
    def estimate_cost(self, prompt: str) -> float:
        """Estimate the cost of executing this prompt."""
        # Default implementation - subclasses can override
        return 0.0
    
    def __str__(self) -> str:
        return f"{self.name} (available: {self.available})"