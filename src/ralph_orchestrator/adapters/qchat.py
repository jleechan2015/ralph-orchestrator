# ABOUTME: Q Chat adapter implementation for q CLI tool
# ABOUTME: Provides integration with q chat command for AI interactions

"""Q Chat adapter for Ralph Orchestrator."""

import subprocess
import os
from typing import Optional
from .base import ToolAdapter, ToolResponse


class QChatAdapter(ToolAdapter):
    """Adapter for Q Chat CLI tool."""
    
    def __init__(self):
        super().__init__("qchat")
        self.command = "q"
    
    def check_availability(self) -> bool:
        """Check if q CLI is available."""
        try:
            # Try to check if q command exists
            result = subprocess.run(
                ["which", "q"],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def execute(self, prompt: str, **kwargs) -> ToolResponse:
        """Execute q chat with the given prompt."""
        if not self.available:
            return ToolResponse(
                success=False,
                output="",
                error="q CLI is not available"
            )
        
        try:
            # Build command - q chat expects the prompt as argument
            cmd = [self.command, "chat", prompt]
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout", 300)  # 5 minute default
            )
            
            if result.returncode == 0:
                return ToolResponse(
                    success=True,
                    output=result.stdout,
                    metadata={"tool": "q chat"}
                )
            else:
                return ToolResponse(
                    success=False,
                    output=result.stdout,
                    error=result.stderr or "q chat command failed"
                )
                
        except subprocess.TimeoutExpired:
            return ToolResponse(
                success=False,
                output="",
                error="q chat command timed out"
            )
        except Exception as e:
            return ToolResponse(
                success=False,
                output="",
                error=str(e)
            )
    
    def estimate_cost(self, prompt: str) -> float:
        """Q chat cost estimation (if applicable)."""
        # Q chat might be free or have different pricing
        # Return 0 for now, can be updated based on actual pricing
        return 0.0