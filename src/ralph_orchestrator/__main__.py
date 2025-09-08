#!/usr/bin/env python3
# ABOUTME: CLI entry point for Ralph Orchestrator with all wrapper functionality
# ABOUTME: Provides complete command-line interface including init, status, and clean commands

"""Command-line interface for Ralph Orchestrator."""

import argparse
import sys
import os
import json
import shutil
from pathlib import Path
import logging
import subprocess
from typing import Optional

# Import the proper orchestrator with adapter support
from .orchestrator import RalphOrchestrator
from .main import (
    RalphConfig, AgentType,
    DEFAULT_MAX_ITERATIONS, DEFAULT_MAX_RUNTIME, DEFAULT_PROMPT_FILE,
    DEFAULT_CHECKPOINT_INTERVAL, DEFAULT_RETRY_DELAY, DEFAULT_MAX_TOKENS,
    DEFAULT_MAX_COST, DEFAULT_CONTEXT_WINDOW, DEFAULT_CONTEXT_THRESHOLD,
    DEFAULT_METRICS_INTERVAL, DEFAULT_MAX_PROMPT_SIZE
)


def init_project():
    """Initialize a new Ralph project."""
    print("Initializing Ralph project...")
    
    # Create directories
    dirs = [
        ".agent/prompts",
        ".agent/checkpoints", 
        ".agent/metrics",
        ".agent/plans",
        ".agent/memory"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create default PROMPT.md if it doesn't exist
    if not Path("PROMPT.md").exists():
        with open("PROMPT.md", "w") as f:
            f.write("""# Task: [Describe your task here]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Success Criteria
- All requirements met
- Tests pass
- Code is clean

<!-- Add TASK_COMPLETE when done -->
""")
        print("Created PROMPT.md template")
    
    # Create default ralph.yml if it doesn't exist
    if not Path("ralph.yml").exists():
        with open("ralph.yml", "w") as f:
            f.write("""# Ralph Orchestrator Configuration
agent: auto
prompt_file: PROMPT.md
max_iterations: 100
max_runtime: 14400
verbose: false

# Adapter configurations
adapters:
  claude:
    enabled: true
    timeout: 300
  q:
    enabled: true
    timeout: 300
  gemini:
    enabled: true
    timeout: 300
""")
        print("Created ralph.yml configuration")
    
    # Initialize git if not already
    if not Path(".git").exists():
        subprocess.run(["git", "init"], capture_output=True)
        print("Initialized git repository")
    
    print("Ralph project initialized!")
    print("Edit ralph.yml to customize configuration")
    print("Edit PROMPT.md to define your task")


def show_status():
    """Show current Ralph project status."""
    print("Ralph Orchestrator Status")
    print("=" * 25)
    
    # Check for PROMPT.md
    if Path("PROMPT.md").exists():
        print(f"Prompt: PROMPT.md exists")
        with open("PROMPT.md", "r") as f:
            content = f.read()
            if "TASK_COMPLETE" in content:
                print(f"Status: TASK COMPLETE")
            else:
                print(f"Status: IN PROGRESS")
    else:
        print(f"Prompt: PROMPT.md not found")
    
    # Check iterations from metrics
    metrics_dir = Path(".agent/metrics")
    if metrics_dir.exists():
        state_files = sorted(metrics_dir.glob("state_*.json"))
        if state_files:
            latest_state = state_files[-1]
            print(f"\nLatest metrics: {latest_state.name}")
            try:
                with open(latest_state, "r") as f:
                    data = json.load(f)
                    print(f"  Iterations: {data.get('iteration_count', 0)}")
                    print(f"  Runtime: {data.get('runtime', 0):.1f}s")
                    print(f"  Errors: {len(data.get('errors', []))}")
            except Exception:
                pass
    
    # Check git status
    if Path(".git").exists():
        print("\nGit checkpoints:")
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout:
            print(result.stdout.strip())
        else:
            print("No checkpoints yet")


def clean_workspace():
    """Clean Ralph workspace."""
    print("Cleaning Ralph workspace...")
    
    # Ask about .agent directory
    response = input("Remove .agent directory? (y/N) ")
    if response.lower() == 'y':
        if Path(".agent").exists():
            shutil.rmtree(".agent")
            print("Removed .agent directory")
    
    # Ask about git reset
    if Path(".git").exists():
        response = input("Reset git to last checkpoint? (y/N) ")
        if response.lower() == 'y':
            subprocess.run(["git", "reset", "--hard", "HEAD"], capture_output=True)
            print("Reset to last checkpoint")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ralph",
        description="Ralph Orchestrator - Put AI in a loop until done",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
    ralph               Run the orchestrator (default)
    ralph init          Initialize a new Ralph project  
    ralph status        Show current Ralph status
    ralph clean         Clean up agent workspace

Configuration:
    Use -c/--config to load settings from a YAML file.
    CLI arguments override config file settings.

Examples:
    ralph                           # Run with auto-detected agent
    ralph -c ralph.yml              # Use configuration file
    ralph -a claude                 # Use Claude agent
    ralph -p task.md -i 50          # Custom prompt, max 50 iterations
    ralph -t 3600 --dry-run         # Test mode with 1 hour timeout
    ralph --max-cost 10.00          # Limit spending to $10
    ralph init                      # Set up new project
    ralph status                    # Check current progress
    ralph clean                     # Clean agent workspace
"""
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Init command
    subparsers.add_parser('init', help='Initialize a new Ralph project')
    
    # Status command
    subparsers.add_parser('status', help='Show current Ralph status')
    
    # Clean command
    subparsers.add_parser('clean', help='Clean up agent workspace')
    
    # Run command (default) - add all the run options
    run_parser = subparsers.add_parser('run', help='Run the orchestrator')
    
    # Core arguments (also at root level for backward compatibility)
    for p in [parser, run_parser]:
        p.add_argument(
            "-c", "--config",
            help="Configuration file (YAML format)"
        )
        
        p.add_argument(
            "-a", "--agent",
            choices=["claude", "q", "gemini", "auto"],
            default="auto",
            help="AI agent to use (default: auto)"
        )
        
        p.add_argument(
            "-p", "--prompt",
            default=DEFAULT_PROMPT_FILE,
            help=f"Prompt file (default: {DEFAULT_PROMPT_FILE})"
        )
        
        p.add_argument(
            "-i", "--iterations", "--max-iterations",
            type=int,
            default=DEFAULT_MAX_ITERATIONS,
            dest="max_iterations",
            help=f"Maximum iterations (default: {DEFAULT_MAX_ITERATIONS})"
        )
        
        p.add_argument(
            "-t", "--time", "--max-runtime",
            type=int,
            default=DEFAULT_MAX_RUNTIME,
            dest="max_runtime",
            help=f"Maximum runtime in seconds (default: {DEFAULT_MAX_RUNTIME})"
        )
        
        p.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        p.add_argument(
            "-d", "--dry-run",
            action="store_true",
            help="Dry run mode (test without execution)"
        )
        
        # Advanced options
        p.add_argument(
            "--max-tokens",
            type=int,
            default=DEFAULT_MAX_TOKENS,
            help=f"Maximum total tokens (default: {DEFAULT_MAX_TOKENS})"
        )
        
        p.add_argument(
            "--max-cost",
            type=float,
            default=DEFAULT_MAX_COST,
            help=f"Maximum cost in USD (default: {DEFAULT_MAX_COST})"
        )
        
        p.add_argument(
            "--context-window",
            type=int,
            default=DEFAULT_CONTEXT_WINDOW,
            help=f"Context window size (default: {DEFAULT_CONTEXT_WINDOW})"
        )
        
        p.add_argument(
            "--context-threshold",
            type=float,
            default=DEFAULT_CONTEXT_THRESHOLD,
            help=f"Context summarization threshold (default: {DEFAULT_CONTEXT_THRESHOLD})"
        )
        
        p.add_argument(
            "--checkpoint-interval",
            type=int,
            default=DEFAULT_CHECKPOINT_INTERVAL,
            help=f"Git checkpoint interval (default: {DEFAULT_CHECKPOINT_INTERVAL})"
        )
        
        p.add_argument(
            "--retry-delay",
            type=int,
            default=DEFAULT_RETRY_DELAY,
            help=f"Retry delay on errors (default: {DEFAULT_RETRY_DELAY})"
        )
        
        p.add_argument(
            "--metrics-interval",
            type=int,
            default=DEFAULT_METRICS_INTERVAL,
            help=f"Metrics logging interval (default: {DEFAULT_METRICS_INTERVAL})"
        )
        
        p.add_argument(
            "--max-prompt-size",
            type=int,
            default=DEFAULT_MAX_PROMPT_SIZE,
            help=f"Max prompt file size (default: {DEFAULT_MAX_PROMPT_SIZE})"
        )
        
        p.add_argument(
            "--no-git",
            action="store_true",
            help="Disable git checkpointing"
        )
        
        p.add_argument(
            "--no-archive",
            action="store_true",
            help="Disable prompt archiving"
        )
        
        p.add_argument(
            "--no-metrics",
            action="store_true",
            help="Disable metrics collection"
        )
        
        p.add_argument(
            "--allow-unsafe-paths",
            action="store_true",
            help="Allow potentially unsafe prompt paths"
        )
        
        # Collect remaining arguments for agent
        p.add_argument(
            "agent_args",
            nargs=argparse.REMAINDER,
            help="Additional arguments to pass to the AI agent"
        )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    command = args.command if args.command else 'run'
    
    if command == 'init':
        init_project()
        sys.exit(0)
    
    if command == 'status':
        show_status()
        sys.exit(0)
    
    if command == 'clean':
        clean_workspace()
        sys.exit(0)
    
    # Run command (default)
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Map agent string to enum
    agent_map = {
        "claude": AgentType.CLAUDE,
        "q": AgentType.Q,
        "gemini": AgentType.GEMINI,
        "auto": AgentType.AUTO
    }
    
    # Create config - load from YAML if provided, otherwise use CLI args
    if args.config:
        try:
            config = RalphConfig.from_yaml(args.config)
            # Override with any CLI arguments that were explicitly provided
            if hasattr(args, 'agent') and args.agent != 'auto':
                config.agent = agent_map[args.agent]
            if hasattr(args, 'verbose') and args.verbose:
                config.verbose = args.verbose
            if hasattr(args, 'dry_run') and args.dry_run:
                config.dry_run = args.dry_run
        except Exception as e:
            print(f"Error loading config file: {e}")
            sys.exit(1)
    else:
        # Create config from CLI arguments
        config = RalphConfig(
            agent=agent_map[args.agent],
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
            agent_args=args.agent_args if hasattr(args, 'agent_args') else []
        )
    
    if config.dry_run:
        print("Dry run mode - no tools will be executed")
        print(f"Configuration:")
        print(f"  Prompt: {config.prompt_file}")
        print(f"  Agent: {config.agent.value}")
        print(f"  Max iterations: {config.max_iterations}")
        print(f"  Max runtime: {config.max_runtime}s")
        print(f"  Max cost: ${config.max_cost:.2f}")
        sys.exit(0)
    
    # Validate prompt file exists
    prompt_path = Path(config.prompt_file)
    if not prompt_path.exists():
        print(f"Error: Prompt file '{config.prompt_file}' not found")
        print("\nPlease create a PROMPT.md file with your task description.")
        print("Example content:")
        print("---")
        print("# Task: Build a simple web server")
        print("")
        print("## Requirements")
        print("- Use Python")
        print("- Include basic routing")
        print("- Add tests")
        print("")
        print("<!-- Add TASK_COMPLETE when done -->")
        print("---")
        sys.exit(1)
    
    try:
        # Create and run orchestrator
        print(f"Starting Ralph Orchestrator...")
        print(f"Agent: {config.agent.value}")
        print(f"Prompt: {config.prompt_file}")
        print(f"Max iterations: {config.max_iterations}")
        print(f"Press Ctrl+C to stop gracefully")
        print("=" * 50)
        
        # Convert RalphConfig to individual parameters for the proper orchestrator
        # Map CLI agent names to orchestrator tool names
        agent_name = config.agent.value if hasattr(config.agent, 'value') else str(config.agent)
        tool_name_map = {
            "q": "qchat",
            "claude": "claude", 
            "gemini": "gemini",
            "auto": "auto"
        }
        primary_tool = tool_name_map.get(agent_name, agent_name)
        
        orchestrator = RalphOrchestrator(
            prompt_file_or_config=config.prompt_file,
            primary_tool=primary_tool,
            max_iterations=config.max_iterations,
            max_runtime=config.max_runtime,
            track_costs=True,  # Enable cost tracking by default
            max_cost=config.max_cost,
            checkpoint_interval=config.checkpoint_interval,
            verbose=config.verbose
        )
        orchestrator.run()
        
        print("=" * 50)
        print("Ralph Orchestrator completed successfully")
        
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()