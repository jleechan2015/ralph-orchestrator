# ABOUTME: Metrics tracking and cost calculation for Ralph Orchestrator
# ABOUTME: Monitors performance, usage, and costs across different AI tools

"""Metrics and cost tracking for Ralph Orchestrator."""

from dataclasses import dataclass, field
from typing import Dict, List
import time
import json


@dataclass
class Metrics:
    """Track orchestration metrics."""
    
    iterations: int = 0
    successful_iterations: int = 0
    failed_iterations: int = 0
    errors: int = 0
    checkpoints: int = 0
    rollbacks: int = 0
    start_time: float = field(default_factory=time.time)
    
    def elapsed_hours(self) -> float:
        """Get elapsed time in hours."""
        return (time.time() - self.start_time) / 3600
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.successful_iterations + self.failed_iterations
        if total == 0:
            return 0.0
        return self.successful_iterations / total
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "iterations": self.iterations,
            "successful_iterations": self.successful_iterations,
            "failed_iterations": self.failed_iterations,
            "errors": self.errors,
            "checkpoints": self.checkpoints,
            "rollbacks": self.rollbacks,
            "elapsed_hours": self.elapsed_hours(),
            "success_rate": self.success_rate()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class CostTracker:
    """Track costs across different AI tools."""
    
    # Cost per 1K tokens (approximate)
    COSTS = {
        "claude": {
            "input": 0.003,   # $3 per 1M input tokens
            "output": 0.015   # $15 per 1M output tokens
        },
        "gemini": {
            "input": 0.00025,  # $0.25 per 1M input tokens
            "output": 0.001    # $1 per 1M output tokens
        },
        "qchat": {
            "input": 0.0,      # Free/local
            "output": 0.0
        },
        "gpt-4": {
            "input": 0.03,     # $30 per 1M input tokens
            "output": 0.06     # $60 per 1M output tokens
        }
    }
    
    def __init__(self):
        """Initialize cost tracker."""
        self.total_cost = 0.0
        self.costs_by_tool: Dict[str, float] = {}
        self.usage_history: List[Dict] = []
    
    def add_usage(
        self,
        tool: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Add usage and calculate cost.
        
        Args:
            tool: Name of the AI tool
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost for this usage
        """
        if tool not in self.COSTS:
            tool = "qchat"  # Default to free tier
        
        costs = self.COSTS[tool]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        total = input_cost + output_cost
        
        # Update tracking
        self.total_cost += total
        if tool not in self.costs_by_tool:
            self.costs_by_tool[tool] = 0.0
        self.costs_by_tool[tool] += total
        
        # Add to history
        self.usage_history.append({
            "timestamp": time.time(),
            "tool": tool,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": total
        })
        
        return total
    
    def get_summary(self) -> Dict:
        """Get cost summary."""
        return {
            "total_cost": self.total_cost,
            "costs_by_tool": self.costs_by_tool,
            "usage_count": len(self.usage_history),
            "average_cost": self.total_cost / len(self.usage_history) if self.usage_history else 0
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.get_summary(), indent=2)