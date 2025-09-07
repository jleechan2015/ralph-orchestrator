# ABOUTME: Claude CLI adapter implementation
# ABOUTME: Provides integration with Anthropic's Claude via command-line interface

"""Claude CLI adapter for Ralph Orchestrator."""

import subprocess
import os
import json
import re
from typing import Optional
from .base import ToolAdapter, ToolResponse


class ClaudeAdapter(ToolAdapter):
    """Adapter for Claude CLI tool."""
    
    def __init__(self):
        self.command = "claude"
        super().__init__("claude")
    
    def check_availability(self) -> bool:
        """Check if Claude CLI is available."""
        try:
            result = subprocess.run(
                [self.command, "--version"],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def execute(self, prompt: str, **kwargs) -> ToolResponse:
        """Execute Claude with the given prompt."""
        if not self.available:
            return ToolResponse(
                success=False,
                output="",
                error="Claude CLI is not available"
            )
        
        try:
            # Build command
            cmd = [self.command, "-p", prompt]
            
            # Add optional parameters
            if kwargs.get("model"):
                cmd.extend(["--model", kwargs["model"]])
            
            if kwargs.get("dangerously_skip_permissions"):
                cmd.append("--dangerously-skip-permissions")
            
            if kwargs.get("output_format"):
                cmd.extend(["--output-format", kwargs["output_format"]])
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout", 300)  # 5 minute default
            )
            
            if result.returncode == 0:
                # Try to extract token count from output if available
                tokens = self._extract_token_count(result.stderr)
                
                return ToolResponse(
                    success=True,
                    output=result.stdout,
                    tokens_used=tokens,
                    cost=self._calculate_cost(tokens),
                    metadata={"model": kwargs.get("model", "claude-3-sonnet")}
                )
            else:
                return ToolResponse(
                    success=False,
                    output=result.stdout,
                    error=result.stderr or "Command failed"
                )
                
        except subprocess.TimeoutExpired:
            return ToolResponse(
                success=False,
                output="",
                error="Claude command timed out"
            )
        except Exception as e:
            return ToolResponse(
                success=False,
                output="",
                error=str(e)
            )
    
    def _extract_token_count(self, stderr: str) -> Optional[int]:
        """Extract token count from Claude stderr output."""
        if not stderr:
            return None
        
        # Look for token count in stderr
        match = re.search(r'tokens?[:\s]+(\d+)', stderr, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        return None
    
    def _calculate_cost(self, tokens: Optional[int]) -> Optional[float]:
        """Calculate estimated cost based on tokens."""
        if not tokens:
            return None
        
        # Claude 3 Sonnet pricing (approximate)
        # $0.003 per 1K input tokens, $0.015 per 1K output tokens
        # Using average for estimation
        cost_per_1k = 0.009
        return (tokens / 1000) * cost_per_1k
    
    def estimate_cost(self, prompt: str) -> float:
        """Estimate cost for the prompt."""
        # Rough estimation: 1 token ≈ 4 characters
        estimated_tokens = len(prompt) / 4
        return self._calculate_cost(estimated_tokens) or 0.0