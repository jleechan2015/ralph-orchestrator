#!/usr/bin/env python3
# ABOUTME: Ralph orchestrator main loop implementation with multi-agent support
# ABOUTME: Implements the core Ralph Wiggum technique with continuous iteration

import sys
import logging
import argparse
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .orchestrator import RalphOrchestrator


# Configuration defaults
DEFAULT_MAX_ITERATIONS = 100
DEFAULT_MAX_RUNTIME = 14400  # 4 hours
DEFAULT_PROMPT_FILE = "PROMPT.md"
DEFAULT_CHECKPOINT_INTERVAL = 5
DEFAULT_RETRY_DELAY = 2
DEFAULT_MAX_TOKENS = 1000000  # 1M tokens total
DEFAULT_MAX_COST = 50.0  # $50 USD
DEFAULT_CONTEXT_WINDOW = 200000  # 200K token context window
DEFAULT_CONTEXT_THRESHOLD = 0.8  # Trigger summarization at 80% of context
DEFAULT_METRICS_INTERVAL = 10  # Log metrics every 10 iterations
DEFAULT_MAX_PROMPT_SIZE = 10485760  # 10MB max prompt file size

# Token costs per million (approximate)
TOKEN_COSTS = {
    "claude": {"input": 3.0, "output": 15.0},  # Claude 3.5 Sonnet
    "q": {"input": 0.5, "output": 1.5},  # Estimated
    "gemini": {"input": 0.5, "output": 1.5}  # Gemini Pro
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ralph-orchestrator')

class AgentType(Enum):
    """Supported AI agent types"""
    CLAUDE = "claude"
    Q = "q"
    GEMINI = "gemini"
    AUTO = "auto"

@dataclass
class AdapterConfig:
    """Configuration for individual adapters"""
    enabled: bool = True
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    timeout: int = 300
    max_retries: int = 3

@dataclass
class RalphConfig:
    """Configuration for Ralph orchestrator"""
    agent: AgentType = AgentType.AUTO
    prompt_file: str = DEFAULT_PROMPT_FILE
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    max_runtime: int = DEFAULT_MAX_RUNTIME
    checkpoint_interval: int = DEFAULT_CHECKPOINT_INTERVAL
    retry_delay: int = DEFAULT_RETRY_DELAY
    archive_prompts: bool = True
    git_checkpoint: bool = True
    verbose: bool = False
    dry_run: bool = False
    max_tokens: int = DEFAULT_MAX_TOKENS
    max_cost: float = DEFAULT_MAX_COST
    context_window: int = DEFAULT_CONTEXT_WINDOW
    context_threshold: float = DEFAULT_CONTEXT_THRESHOLD
    metrics_interval: int = DEFAULT_METRICS_INTERVAL
    enable_metrics: bool = True
    max_prompt_size: int = DEFAULT_MAX_PROMPT_SIZE
    allow_unsafe_paths: bool = False
    agent_args: List[str] = field(default_factory=list)
    adapters: Dict[str, AdapterConfig] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'RalphConfig':
        """Load configuration from YAML file"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Convert agent string to AgentType enum
        if 'agent' in config_data:
            config_data['agent'] = AgentType(config_data['agent'])
        
        # Process adapter configurations
        if 'adapters' in config_data:
            adapter_configs = {}
            for name, adapter_data in config_data['adapters'].items():
                if isinstance(adapter_data, dict):
                    adapter_configs[name] = AdapterConfig(**adapter_data)
                else:
                    # Simple boolean enable/disable
                    adapter_configs[name] = AdapterConfig(enabled=bool(adapter_data))
            config_data['adapters'] = adapter_configs
        
        # Filter out unknown keys
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in config_data.items() if k in valid_keys}
        
        return cls(**filtered_data)
    
    def get_adapter_config(self, adapter_name: str) -> AdapterConfig:
        """Get configuration for a specific adapter"""
        return self.adapters.get(adapter_name, AdapterConfig())

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum Orchestrator - Put AI in a loop until done"
    )
    
    parser.add_argument(
        "--agent", "-a",
        type=str,
        choices=["codex", "claude", "q", "gemini", "auto"],
        default="codex",
        help="AI agent to use (default: codex)"
    )
    
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        default=DEFAULT_PROMPT_FILE,
        help="Prompt file path (default: PROMPT.md)"
    )
    
    parser.add_argument(
        "--max-iterations", "-i",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"Maximum iterations (default: {DEFAULT_MAX_ITERATIONS})"
    )
    
    parser.add_argument(
        "--max-runtime", "-t",
        type=int,
        default=DEFAULT_MAX_RUNTIME,
        help=f"Maximum runtime in seconds (default: {DEFAULT_MAX_RUNTIME})"
    )
    
    parser.add_argument(
        "--checkpoint-interval", "-c",
        type=int,
        default=DEFAULT_CHECKPOINT_INTERVAL,
        help=f"Checkpoint interval (default: {DEFAULT_CHECKPOINT_INTERVAL})"
    )
    
    parser.add_argument(
        "--retry-delay", "-r",
        type=int,
        default=DEFAULT_RETRY_DELAY,
        help=f"Retry delay in seconds (default: {DEFAULT_RETRY_DELAY})"
    )
    
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum total tokens (default: {DEFAULT_MAX_TOKENS:,})"
    )
    
    parser.add_argument(
        "--max-cost",
        type=float,
        default=DEFAULT_MAX_COST,
        help=f"Maximum cost in USD (default: ${DEFAULT_MAX_COST:.2f})"
    )
    
    parser.add_argument(
        "--context-window",
        type=int,
        default=DEFAULT_CONTEXT_WINDOW,
        help=f"Context window size in tokens (default: {DEFAULT_CONTEXT_WINDOW:,})"
    )
    
    parser.add_argument(
        "--context-threshold",
        type=float,
        default=DEFAULT_CONTEXT_THRESHOLD,
        help=f"Context summarization threshold (default: {DEFAULT_CONTEXT_THRESHOLD:.1f} = {DEFAULT_CONTEXT_THRESHOLD*100:.0f}%%)"
    )
    
    parser.add_argument(
        "--metrics-interval",
        type=int,
        default=DEFAULT_METRICS_INTERVAL,
        help=f"Metrics logging interval (default: {DEFAULT_METRICS_INTERVAL})"
    )
    
    parser.add_argument(
        "--no-metrics",
        action="store_true",
        help="Disable metrics collection"
    )
    
    parser.add_argument(
        "--max-prompt-size",
        type=int,
        default=DEFAULT_MAX_PROMPT_SIZE,
        help=f"Maximum prompt file size in bytes (default: {DEFAULT_MAX_PROMPT_SIZE})"
    )
    
    parser.add_argument(
        "--allow-unsafe-paths",
        action="store_true",
        help="Allow potentially unsafe prompt paths (use with caution)"
    )
    
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Disable git checkpointing"
    )
    
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Disable prompt archiving"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (don't execute agents)"
    )
    
    parser.add_argument(
        "agent_args",
        nargs="*",
        help="Additional arguments to pass to the AI agent"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create config
    config = RalphConfig(
        agent=AgentType(args.agent),
        prompt_file=args.prompt,
        max_iterations=args.max_iterations,
        max_runtime=args.max_runtime,
        checkpoint_interval=args.checkpoint_interval,
        retry_delay=args.retry_delay,
        archive_prompts=not args.no_archive,
        git_checkpoint=not args.no_git,
        verbose=args.verbose,
        dry_run=args.dry_run,
        max_tokens=args.max_tokens,
        max_cost=args.max_cost,
        context_window=args.context_window,
        context_threshold=args.context_threshold,
        metrics_interval=args.metrics_interval,
        enable_metrics=not args.no_metrics,
        max_prompt_size=args.max_prompt_size,
        allow_unsafe_paths=args.allow_unsafe_paths,
        agent_args=args.agent_args
    )
    
    # Run orchestrator
    orchestrator = RalphOrchestrator(config)
    return orchestrator.run()

if __name__ == "__main__":
    sys.exit(main())