#!/usr/bin/env python3
# ABOUTME: Ralph orchestrator main loop implementation with multi-agent support
# ABOUTME: Implements the core Ralph Wiggum technique with continuous iteration

import subprocess
import time
import os
import sys
import json
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

# Configuration defaults
DEFAULT_MAX_ITERATIONS = 100
DEFAULT_MAX_RUNTIME = 14400  # 4 hours
DEFAULT_PROMPT_FILE = "PROMPT.md"
DEFAULT_CHECKPOINT_INTERVAL = 5
DEFAULT_RETRY_DELAY = 2

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
    agent_args: List[str] = field(default_factory=list)

class RalphOrchestrator:
    """Main orchestrator for Ralph Wiggum technique"""
    
    def __init__(self, config: RalphConfig):
        self.config = config
        self.iteration_count = 0
        self.start_time = time.time()
        self.errors = []
        self.checkpoints = []
        self.setup_signal_handlers()
        self.setup_directories()
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info(f"Received shutdown signal {signum}")
        self.save_state()
        sys.exit(0)
        
    def setup_directories(self):
        """Create necessary directories"""
        dirs = [
            Path(".agent"),
            Path(".agent/prompts"),
            Path(".agent/checkpoints"),
            Path(".agent/metrics")
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            
    def detect_agent(self) -> AgentType:
        """Auto-detect available AI agent"""
        agents = [
            (AgentType.CLAUDE, ["claude", "--version"]),
            (AgentType.Q, ["q", "--version"]),
            (AgentType.GEMINI, ["gemini", "--version"])
        ]
        
        for agent_type, cmd in agents:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    logger.info(f"Detected {agent_type.value} agent")
                    return agent_type
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
                
        raise RuntimeError("No AI agent found. Please install claude, q, or gemini CLI")
        
    def build_agent_command(self) -> List[str]:
        """Build the command for the AI agent"""
        agent = self.config.agent
        if agent == AgentType.AUTO:
            agent = self.detect_agent()
            
        prompt_file = Path(self.config.prompt_file)
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
            
        if agent == AgentType.CLAUDE:
            cmd = ["claude", "-p", f"@{prompt_file}"]
        elif agent == AgentType.Q:
            cmd = ["q", "chat", "-f", str(prompt_file)]
        elif agent == AgentType.GEMINI:
            cmd = ["gemini", "-p", f"@{prompt_file}"]
        else:
            raise ValueError(f"Unsupported agent type: {agent}")
            
        # Add any additional agent arguments
        cmd.extend(self.config.agent_args)
        return cmd
        
    def check_completion(self) -> bool:
        """Check if task is marked as complete"""
        prompt_file = Path(self.config.prompt_file)
        if prompt_file.exists():
            content = prompt_file.read_text()
            return "TASK_COMPLETE" in content
        return False
        
    def run_iteration(self) -> bool:
        """Run a single iteration of the Ralph loop"""
        self.iteration_count += 1
        logger.info(f"Iteration {self.iteration_count} starting...")
        
        try:
            cmd = self.build_agent_command()
            
            if self.config.dry_run:
                logger.info(f"[DRY RUN] Would execute: {' '.join(cmd)}")
                return True
                
            # Execute the AI agent
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per iteration
            )
            
            if result.returncode != 0:
                error_msg = f"Agent failed with code {result.returncode}: {result.stderr}"
                logger.error(error_msg)
                self.errors.append({
                    'iteration': self.iteration_count,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
                return False
                
            # Check for completion
            if self.check_completion():
                logger.info("Task marked as complete!")
                return True
                
            # Checkpoint if needed
            if self.iteration_count % self.config.checkpoint_interval == 0:
                self.create_checkpoint()
                
        except subprocess.TimeoutExpired:
            logger.error("Agent execution timed out")
            self.errors.append({
                'iteration': self.iteration_count,
                'error': 'Timeout',
                'timestamp': datetime.now().isoformat()
            })
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.errors.append({
                'iteration': self.iteration_count,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return False
            
        return None  # Continue iterating
        
    def create_checkpoint(self):
        """Create a checkpoint of current state"""
        if self.config.git_checkpoint:
            try:
                subprocess.run(["git", "add", "-A"], check=True)
                subprocess.run(
                    ["git", "commit", "-m", f"Ralph checkpoint: iteration {self.iteration_count}"],
                    check=True
                )
                logger.info(f"Created git checkpoint at iteration {self.iteration_count}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to create git checkpoint: {e}")
                
        # Archive prompt if it changed
        if self.config.archive_prompts:
            prompt_file = Path(self.config.prompt_file)
            if prompt_file.exists():
                archive_path = Path(f".agent/prompts/prompt_{self.iteration_count:04d}.md")
                archive_path.write_text(prompt_file.read_text())
                
        self.checkpoints.append({
            'iteration': self.iteration_count,
            'timestamp': datetime.now().isoformat()
        })
        
    def save_state(self):
        """Save current orchestrator state"""
        state = {
            'iteration_count': self.iteration_count,
            'start_time': self.start_time,
            'runtime': time.time() - self.start_time,
            'errors': self.errors,
            'checkpoints': self.checkpoints,
            'config': {
                'agent': self.config.agent.value,
                'prompt_file': self.config.prompt_file,
                'max_iterations': self.config.max_iterations,
                'max_runtime': self.config.max_runtime
            }
        }
        
        state_file = Path(f".agent/metrics/state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        state_file.write_text(json.dumps(state, indent=2))
        logger.info(f"Saved state to {state_file}")
        
    def should_continue(self) -> bool:
        """Check if loop should continue"""
        # Check iteration limit
        if self.iteration_count >= self.config.max_iterations:
            logger.info(f"Reached max iterations ({self.config.max_iterations})")
            return False
            
        # Check runtime limit
        runtime = time.time() - self.start_time
        if runtime >= self.config.max_runtime:
            logger.info(f"Reached max runtime ({self.config.max_runtime}s)")
            return False
            
        # Check for too many consecutive errors
        recent_errors = [e for e in self.errors if e['iteration'] > self.iteration_count - 5]
        if len(recent_errors) >= 5:
            logger.error("Too many consecutive errors, stopping")
            return False
            
        return True
        
    def run(self):
        """Main orchestration loop"""
        logger.info(f"Starting Ralph orchestrator with {self.config.agent.value} agent")
        logger.info(f"Prompt file: {self.config.prompt_file}")
        logger.info(f"Max iterations: {self.config.max_iterations}")
        logger.info(f"Max runtime: {self.config.max_runtime}s")
        
        while self.should_continue():
            result = self.run_iteration()
            
            if result is True:
                # Task completed successfully
                logger.info("Task completed successfully!")
                self.save_state()
                return 0
            elif result is False:
                # Error occurred, retry after delay
                logger.info(f"Retrying in {self.config.retry_delay}s...")
                time.sleep(self.config.retry_delay)
            else:
                # Continue to next iteration
                time.sleep(1)  # Brief pause between iterations
                
        # Loop ended without completion
        logger.warning("Loop ended without task completion")
        self.save_state()
        return 1

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum Orchestrator - Put AI in a loop until done"
    )
    
    parser.add_argument(
        "--agent", "-a",
        type=str,
        choices=["claude", "q", "gemini", "auto"],
        default="auto",
        help="AI agent to use (default: auto-detect)"
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
        agent_args=args.agent_args
    )
    
    # Run orchestrator
    orchestrator = RalphOrchestrator(config)
    return orchestrator.run()

if __name__ == "__main__":
    sys.exit(main())