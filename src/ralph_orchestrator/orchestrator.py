# ABOUTME: Core orchestration loop implementing the Ralph Wiggum technique
# ABOUTME: Manages AI agent execution with safety, metrics, and recovery

"""Core orchestration loop for Ralph Orchestrator."""

import os
import sys
import time
import signal
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
import json
from datetime import datetime

from .adapters.base import ToolAdapter, ToolResponse
from .adapters.claude import ClaudeAdapter
from .adapters.qchat import QChatAdapter
from .adapters.gemini import GeminiAdapter
from .metrics import Metrics, CostTracker
from .safety import SafetyGuard
from .context import ContextManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ralph-orchestrator')


class RalphOrchestrator:
    """Main orchestration loop for AI agents."""
    
    def __init__(
        self,
        prompt_file: str = "PROMPT.md",
        primary_tool: str = "claude",
        max_iterations: int = 100,
        max_runtime: int = 14400,
        track_costs: bool = False,
        max_cost: float = 10.0,
        checkpoint_interval: int = 5,
        archive_dir: str = "./prompts/archive"
    ):
        """Initialize the orchestrator.
        
        Args:
            prompt_file: Path to the prompt file
            primary_tool: Primary AI tool to use (claude, qchat, gemini)
            max_iterations: Maximum number of iterations
            max_runtime: Maximum runtime in seconds
            track_costs: Whether to track costs
            max_cost: Maximum allowed cost
            checkpoint_interval: Git checkpoint frequency
            archive_dir: Directory for prompt archives
        """
        self.prompt_file = Path(prompt_file)
        self.primary_tool = primary_tool
        self.max_iterations = max_iterations
        self.max_runtime = max_runtime
        self.track_costs = track_costs
        self.max_cost = max_cost
        self.checkpoint_interval = checkpoint_interval
        self.archive_dir = Path(archive_dir)
        
        # Initialize components
        self.metrics = Metrics()
        self.cost_tracker = CostTracker() if track_costs else None
        self.safety_guard = SafetyGuard(max_iterations, max_runtime, max_cost)
        self.context_manager = ContextManager(self.prompt_file)
        
        # Initialize adapters
        self.adapters = self._initialize_adapters()
        self.current_adapter = self.adapters.get(primary_tool)
        
        if not self.current_adapter:
            raise ValueError(f"Unknown tool: {primary_tool}")
        
        # Signal handling
        self.stop_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Create directories
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        Path(".ralph").mkdir(exist_ok=True)
        
        logger.info(f"Ralph Orchestrator initialized with {primary_tool}")
    
    def _initialize_adapters(self) -> Dict[str, ToolAdapter]:
        """Initialize available adapters."""
        adapters = {}
        
        # Try to initialize each adapter
        try:
            adapter = ClaudeAdapter()
            if adapter.available:
                adapters['claude'] = adapter
                logger.info("Claude adapter initialized")
            else:
                logger.warning("Claude CLI not available")
        except Exception as e:
            logger.warning(f"Claude adapter error: {e}")
        
        try:
            adapter = QChatAdapter()
            if adapter.available:
                adapters['qchat'] = adapter
                logger.info("Q Chat adapter initialized")
            else:
                logger.warning("Q Chat CLI not available")
        except Exception as e:
            logger.warning(f"Q Chat adapter error: {e}")
        
        try:
            adapter = GeminiAdapter()
            if adapter.available:
                adapters['gemini'] = adapter
                logger.info("Gemini adapter initialized")
            else:
                logger.warning("Gemini CLI not available")
        except Exception as e:
            logger.warning(f"Gemini adapter error: {e}")
        
        return adapters
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop_requested = True
    
    def run(self) -> None:
        """Run the main orchestration loop."""
        logger.info("Starting Ralph orchestration loop")
        start_time = time.time()
        
        while not self.stop_requested:
            # Check safety limits
            safety_check = self.safety_guard.check(
                self.metrics.iterations,
                time.time() - start_time,
                self.cost_tracker.total_cost if self.cost_tracker else 0
            )
            
            if not safety_check.passed:
                logger.warning(f"Safety limit reached: {safety_check.reason}")
                break
            
            # Check for task completion
            if self._is_task_complete():
                logger.info("Task marked as complete")
                break
            
            # Execute iteration
            self.metrics.iterations += 1
            logger.info(f"Starting iteration {self.metrics.iterations}")
            
            try:
                success = self._execute_iteration()
                
                if success:
                    self.metrics.successful_iterations += 1
                else:
                    self.metrics.failed_iterations += 1
                    self._handle_failure()
                
                # Checkpoint if needed
                if self.metrics.iterations % self.checkpoint_interval == 0:
                    self._create_checkpoint()
                
            except Exception as e:
                logger.error(f"Error in iteration: {e}")
                self.metrics.errors += 1
                self._handle_error(e)
            
            # Brief pause between iterations
            time.sleep(2)
        
        # Final summary
        self._print_summary()
    
    def _is_task_complete(self) -> bool:
        """Check if the task is marked as complete."""
        if not self.prompt_file.exists():
            return False
        
        content = self.prompt_file.read_text()
        # Look for TASK_COMPLETE marker in various forms
        for line in content.split('\n'):
            line_stripped = line.strip()
            # Check for HTML comment style
            if '<!-- TASK_COMPLETE -->' in line:
                return True
            # Look for TASK_COMPLETE as a standalone marker, not in instructions
            if line_stripped == 'TASK_COMPLETE' or line_stripped == '**TASK_COMPLETE**':
                return True
            # Also check for markdown checkbox style
            if line_stripped == '- [x] TASK_COMPLETE' or line_stripped == '[x] TASK_COMPLETE':
                return True
        return False
    
    def _execute_iteration(self) -> bool:
        """Execute a single iteration."""
        # Get the current prompt
        prompt = self.context_manager.get_prompt()
        
        # Try primary adapter with prompt file path
        response = self.current_adapter.execute(
            prompt, 
            prompt_file=str(self.prompt_file)
        )
        
        if not response.success and len(self.adapters) > 1:
            # Try fallback adapters
            for name, adapter in self.adapters.items():
                if adapter != self.current_adapter:
                    logger.info(f"Falling back to {name}")
                    response = adapter.execute(
                        prompt,
                        prompt_file=str(self.prompt_file)
                    )
                    if response.success:
                        break
        
        # Track costs if enabled
        if self.cost_tracker and response.success:
            if response.tokens_used:
                tokens = response.tokens_used
            else:
                tokens = self._estimate_tokens(response.output)
            
            cost = self.cost_tracker.add_usage(
                self.current_adapter.name,
                tokens,
                tokens // 4  # Rough output estimate
            )
            logger.info(f"Estimated cost: ${cost:.4f} (total: ${self.cost_tracker.total_cost:.4f})")
        
        # Update context if needed
        if response.success and len(response.output) > 1000:
            self.context_manager.update_context(response.output)
        
        return response.success
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text."""
        # Rough estimate: 1 token per 4 characters
        return len(text) // 4
    
    def _handle_failure(self):
        """Handle iteration failure."""
        logger.warning("Iteration failed, attempting recovery")
        
        # Simple exponential backoff
        backoff = min(2 ** self.metrics.failed_iterations, 60)
        logger.info(f"Backing off for {backoff} seconds")
        time.sleep(backoff)
        
        # Consider rollback after multiple failures
        if self.metrics.failed_iterations > 3:
            self._rollback_checkpoint()
    
    def _handle_error(self, error: Exception):
        """Handle iteration error."""
        logger.error(f"Handling error: {error}")
        
        # Archive current prompt
        self._archive_prompt()
        
        # Reset if too many errors
        if self.metrics.errors > 5:
            logger.warning("Too many errors, resetting state")
            self._reset_state()
    
    def _create_checkpoint(self):
        """Create a git checkpoint."""
        try:
            subprocess.run(
                ["git", "add", "-A"],
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", f"Ralph checkpoint {self.metrics.iterations}"],
                check=True,
                capture_output=True
            )
            self.metrics.checkpoints += 1
            logger.info(f"Created checkpoint {self.metrics.checkpoints}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to create checkpoint: {e}")
    
    def _rollback_checkpoint(self):
        """Rollback to previous checkpoint."""
        try:
            subprocess.run(
                ["git", "reset", "--hard", "HEAD~1"],
                check=True,
                capture_output=True
            )
            logger.info("Rolled back to previous checkpoint")
            self.metrics.rollbacks += 1
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to rollback: {e}")
    
    def _archive_prompt(self):
        """Archive the current prompt."""
        if not self.prompt_file.exists():
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = self.archive_dir / f"prompt_{timestamp}.md"
        
        try:
            archive_path.write_text(self.prompt_file.read_text())
            logger.info(f"Archived prompt to {archive_path}")
        except Exception as e:
            logger.error(f"Failed to archive prompt: {e}")
    
    def _reset_state(self):
        """Reset the orchestrator state."""
        logger.info("Resetting orchestrator state")
        self.metrics = Metrics()
        if self.cost_tracker:
            self.cost_tracker = CostTracker()
        self.context_manager.reset()
    
    def _print_summary(self):
        """Print execution summary."""
        logger.info("=" * 50)
        logger.info("Ralph Orchestration Summary")
        logger.info("=" * 50)
        logger.info(f"Total iterations: {self.metrics.iterations}")
        logger.info(f"Successful: {self.metrics.successful_iterations}")
        logger.info(f"Failed: {self.metrics.failed_iterations}")
        logger.info(f"Errors: {self.metrics.errors}")
        logger.info(f"Checkpoints: {self.metrics.checkpoints}")
        logger.info(f"Rollbacks: {self.metrics.rollbacks}")
        
        if self.cost_tracker:
            logger.info(f"Total cost: ${self.cost_tracker.total_cost:.4f}")
            logger.info("Cost breakdown:")
            for tool, cost in self.cost_tracker.costs_by_tool.items():
                logger.info(f"  {tool}: ${cost:.4f}")
        
        # Save metrics to file
        metrics_file = Path(".ralph") / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        metrics_data = {
            "iterations": self.metrics.iterations,
            "successful": self.metrics.successful_iterations,
            "failed": self.metrics.failed_iterations,
            "errors": self.metrics.errors,
            "checkpoints": self.metrics.checkpoints,
            "rollbacks": self.metrics.rollbacks,
        }
        
        if self.cost_tracker:
            metrics_data["cost"] = {
                "total": self.cost_tracker.total_cost,
                "by_tool": self.cost_tracker.costs_by_tool
            }
        
        metrics_file.write_text(json.dumps(metrics_data, indent=2))
        logger.info(f"Metrics saved to {metrics_file}")