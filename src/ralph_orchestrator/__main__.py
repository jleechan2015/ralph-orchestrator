# ABOUTME: CLI entry point for Ralph Orchestrator
# ABOUTME: Provides command-line interface for running the orchestration loop

"""Command-line interface for Ralph Orchestrator."""

import argparse
import sys
import os
from pathlib import Path
import logging

from .orchestrator import RalphOrchestrator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ralph Orchestrator - Simple AI agent orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with Claude (default)
  ralph-orchestrator
  
  # Use Q Chat as primary tool
  ralph-orchestrator --tool qchat
  
  # Enable cost tracking with limits
  ralph-orchestrator --track-costs --max-cost 1.00
  
  # Custom prompt file and iterations
  ralph-orchestrator --prompt TASK.md --max-iterations 50
  
  # Debug mode with verbose output
  ralph-orchestrator --verbose --dry-run
        """
    )
    
    # Core arguments
    parser.add_argument(
        "--prompt",
        default="PROMPT.md",
        help="Path to the prompt file (default: PROMPT.md)"
    )
    
    parser.add_argument(
        "--tool",
        choices=["claude", "qchat", "gemini"],
        default=os.getenv("RALPH_PRIMARY_TOOL", "claude"),
        help="Primary AI tool to use (default: claude)"
    )
    
    # Limits
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=int(os.getenv("RALPH_MAX_ITERATIONS", "100")),
        help="Maximum number of iterations (default: 100)"
    )
    
    parser.add_argument(
        "--max-runtime",
        type=int,
        default=int(os.getenv("RALPH_MAX_RUNTIME", "14400")),
        help="Maximum runtime in seconds (default: 14400 = 4 hours)"
    )
    
    parser.add_argument(
        "--max-cost",
        type=float,
        default=10.0,
        help="Maximum allowed cost in dollars (default: 10.00)"
    )
    
    # Cost tracking
    parser.add_argument(
        "--track-costs",
        action="store_true",
        help="Enable cost tracking and estimation"
    )
    
    # Checkpointing
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=5,
        help="Git checkpoint frequency (default: every 5 iterations)"
    )
    
    parser.add_argument(
        "--archive-dir",
        default="./prompts/archive",
        help="Directory for prompt archives (default: ./prompts/archive)"
    )
    
    # Debugging
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without executing tools"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Validate prompt file exists
    prompt_path = Path(args.prompt)
    if not prompt_path.exists():
        print(f"Error: Prompt file '{args.prompt}' not found")
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
        print("<!-- Add TASK_COMPLETE here when done -->")
        print("---")
        sys.exit(1)
    
    if args.dry_run:
        print("Dry run mode - no tools will be executed")
        print(f"Configuration:")
        print(f"  Prompt: {args.prompt}")
        print(f"  Tool: {args.tool}")
        print(f"  Max iterations: {args.max_iterations}")
        print(f"  Max runtime: {args.max_runtime}s")
        print(f"  Track costs: {args.track_costs}")
        print(f"  Max cost: ${args.max_cost:.2f}")
        sys.exit(0)
    
    try:
        # Create orchestrator
        orchestrator = RalphOrchestrator(
            prompt_file=args.prompt,
            primary_tool=args.tool,
            max_iterations=args.max_iterations,
            max_runtime=args.max_runtime,
            track_costs=args.track_costs,
            max_cost=args.max_cost,
            checkpoint_interval=args.checkpoint_interval,
            archive_dir=args.archive_dir
        )
        
        # Run the orchestration loop
        print(f"Starting Ralph Orchestrator with {args.tool}")
        print(f"Prompt: {args.prompt}")
        print(f"Max iterations: {args.max_iterations}")
        print(f"Press Ctrl+C to stop gracefully")
        print("-" * 50)
        
        orchestrator.run()
        
        print("-" * 50)
        print("Ralph Orchestrator completed successfully")
        
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()