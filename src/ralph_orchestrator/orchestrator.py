# ABOUTME: Core orchestration loop implementing the Ralph Wiggum technique
# ABOUTME: Manages AI agent execution with safety, metrics, and recovery

"""Core orchestration loop for Ralph Orchestrator."""

import os
import sys
import time
import signal
import logging
import subprocess
import asyncio
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
        prompt_file_or_config = None,
        primary_tool: str = "claude",
        max_iterations: int = 100,
        max_runtime: int = 14400,
        track_costs: bool = False,
        max_cost: float = 10.0,
        checkpoint_interval: int = 5,
        archive_dir: str = "./prompts/archive",
        verbose: bool = False
    ):
        """Initialize the orchestrator.
        
        Args:
            prompt_file_or_config: Path to prompt file or RalphConfig object
            primary_tool: Primary AI tool to use (claude, qchat, gemini)
            max_iterations: Maximum number of iterations
            max_runtime: Maximum runtime in seconds
            track_costs: Whether to track costs
            max_cost: Maximum allowed cost
            checkpoint_interval: Git checkpoint frequency
            archive_dir: Directory for prompt archives
            verbose: Enable verbose logging output
        """
        # Handle both config object and individual parameters
        if hasattr(prompt_file_or_config, 'prompt_file'):
            # It's a config object
            config = prompt_file_or_config
            self.prompt_file = Path(config.prompt_file)
            self.primary_tool = config.agent.value if hasattr(config.agent, 'value') else str(config.agent)
            self.max_iterations = config.max_iterations
            self.max_runtime = config.max_runtime
            self.track_costs = hasattr(config, 'max_cost') and config.max_cost > 0
            self.max_cost = config.max_cost if hasattr(config, 'max_cost') else max_cost
            self.checkpoint_interval = config.checkpoint_interval
            self.archive_dir = Path(config.archive_dir if hasattr(config, 'archive_dir') else archive_dir)
            self.verbose = config.verbose if hasattr(config, 'verbose') else False
        else:
            # Individual parameters
            self.prompt_file = Path(prompt_file_or_config if prompt_file_or_config else "PROMPT.md")
            self.primary_tool = primary_tool
            self.max_iterations = max_iterations
            self.max_runtime = max_runtime
            self.track_costs = track_costs
            self.max_cost = max_cost
            self.checkpoint_interval = checkpoint_interval
            self.archive_dir = Path(archive_dir)
            self.verbose = verbose
        
        # Initialize components
        self.metrics = Metrics()
        self.cost_tracker = CostTracker() if track_costs else None
        self.safety_guard = SafetyGuard(max_iterations, max_runtime, max_cost)
        self.context_manager = ContextManager(self.prompt_file)
        
        # Initialize adapters
        self.adapters = self._initialize_adapters()

        # Map CLI agent names to adapter names
        agent_mapping = {
            'codex': 'codex',
            'q': 'qchat',
            'claude': 'claude',
            'gemini': 'gemini'
        }

        adapter_name = agent_mapping.get(primary_tool, primary_tool)
        self.current_adapter = self.adapters.get(adapter_name)

        if not self.current_adapter:
            available_agents = list(agent_mapping.keys())
            raise ValueError(f"Unknown tool: {primary_tool}. Available agents: {available_agents}")
        
        # Signal handling
        self.stop_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Task queue tracking
        self.task_queue = []  # List of pending tasks extracted from prompt
        self.current_task = None  # Currently executing task
        self.completed_tasks = []  # List of completed tasks with results
        self.task_start_time = None  # Start time of current task
        
        # Create directories
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        Path(".agent").mkdir(exist_ok=True)
        
        logger.info(f"Ralph Orchestrator initialized with {primary_tool}")
    
    def _initialize_adapters(self) -> Dict[str, ToolAdapter]:
        """Initialize available adapters."""
        adapters = {}
        
        # Try to initialize each adapter
        try:
            from .adapters.codex import CodexAdapter
            adapter = CodexAdapter(verbose=self.verbose)
            if adapter.available:
                adapters['codex'] = adapter
                logger.info("Codex adapter initialized")
            else:
                logger.warning("Codex CLI not available")
        except Exception as e:
            logger.warning(f"Codex adapter error: {e}")

        try:
            adapter = ClaudeAdapter(verbose=self.verbose)
            if adapter.available:
                adapters['claude'] = adapter
                logger.info("Claude adapter initialized")
            else:
                logger.warning("Claude SDK not available")
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
        # Create event loop if needed and run async version
        try:
            asyncio.run(self.arun())
        except RuntimeError:
            # If loop already exists, use it
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.arun())
    
    async def arun(self) -> None:
        """Run the main orchestration loop asynchronously."""
        logger.info("Starting Ralph orchestration loop")
        start_time = time.time()
        self._start_time = start_time  # Store for state retrieval
        
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
            
            # No longer checking for task completion - run until limits
            
            # Execute iteration
            self.metrics.iterations += 1
            logger.info(f"Starting iteration {self.metrics.iterations}")
            
            try:
                success = await self._aexecute_iteration()
                
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
            await asyncio.sleep(2)
        
        # Final summary
        self._print_summary()
    
    
    def _execute_iteration(self) -> bool:
        """Execute a single iteration (sync wrapper)."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._aexecute_iteration())
        except RuntimeError:
            # Create new event loop if needed
            return asyncio.run(self._aexecute_iteration())
    
    async def _aexecute_iteration(self) -> bool:
        """Execute a single iteration asynchronously."""
        # Get the current prompt
        prompt = self.context_manager.get_prompt()
        
        # Extract tasks from prompt if task queue is empty
        if not self.task_queue and not self.current_task:
            self._extract_tasks_from_prompt(prompt)
        
        # Update current task status
        self._update_current_task('in_progress')
        
        # Try primary adapter with prompt file path
        response = await self.current_adapter.aexecute(
            prompt, 
            prompt_file=str(self.prompt_file),
            verbose=self.verbose
        )
        
        if not response.success and len(self.adapters) > 1:
            # Try fallback adapters
            for name, adapter in self.adapters.items():
                if adapter != self.current_adapter:
                    logger.info(f"Falling back to {name}")
                    response = await adapter.aexecute(
                        prompt,
                        prompt_file=str(self.prompt_file),
                        verbose=self.verbose
                    )
                    if response.success:
                        break
        
        # Log the response output (already streamed to console if verbose)
        if response.success and response.output:
            # Log a preview for the logs
            output_preview = response.output[:500] if len(response.output) > 500 else response.output
            logger.debug(f"Agent response preview: {output_preview}")
            if len(response.output) > 500:
                logger.debug(f"... (total {len(response.output)} characters)")
        
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
        
        # Update task status based on response
        if response.success and self.current_task:
            # Check if response indicates task completion
            output_lower = response.output.lower() if response.output else ""
            if any(word in output_lower for word in ['completed', 'finished', 'done', 'committed']):
                self._update_current_task('completed')
        
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
        metrics_dir = Path(".agent") / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        metrics_file = metrics_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    
    def _extract_tasks_from_prompt(self, prompt: str):
        """Extract tasks from the prompt text."""
        import re
        
        # Look for task patterns in the prompt
        # Common patterns: "- [ ] task", "1. task", "Task: description"
        task_patterns = [
            r'^\s*-\s*\[\s*\]\s*(.+)$',  # Checkbox tasks
            r'^\s*\d+\.\s*(.+)$',  # Numbered tasks
            r'^Task:\s*(.+)$',  # Task: format
            r'^TODO:\s*(.+)$',  # TODO: format
        ]
        
        lines = prompt.split('\n')
        for line in lines:
            for pattern in task_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    task = {
                        'id': len(self.task_queue) + len(self.completed_tasks) + 1,
                        'description': match.group(1).strip(),
                        'status': 'pending',
                        'created_at': datetime.now().isoformat(),
                        'completed_at': None,
                        'iteration': None
                    }
                    self.task_queue.append(task)
                    break
        
        # If no tasks found, create a general task
        if not self.task_queue and not self.completed_tasks:
            self.task_queue.append({
                'id': 1,
                'description': 'Execute orchestrator instructions',
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'completed_at': None,
                'iteration': None
            })
    
    def _update_current_task(self, status: str = 'in_progress'):
        """Update the current task status."""
        if not self.current_task and self.task_queue:
            self.current_task = self.task_queue.pop(0)
            self.current_task['status'] = 'in_progress'
            self.current_task['iteration'] = self.metrics.iterations
            self.task_start_time = time.time()
        elif self.current_task:
            self.current_task['status'] = status
            if status == 'completed':
                self.current_task['completed_at'] = datetime.now().isoformat()
                self.completed_tasks.append(self.current_task)
                self.current_task = None
                self.task_start_time = None
    
    def _reload_prompt(self):
        """Reload the prompt file to pick up any changes."""
        logger.info("Reloading prompt file due to external update")
        # The context manager will automatically reload on next get_prompt() call
        # Clear the context manager's cache to force reload
        if hasattr(self.context_manager, '_load_initial_prompt'):
            self.context_manager._load_initial_prompt()
        
        # Extract new tasks if the prompt has changed significantly
        prompt = self.context_manager.get_prompt()
        
        # Only re-extract tasks if we don't have a current task or queue
        if not self.current_task and not self.task_queue:
            self._extract_tasks_from_prompt(prompt)
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get current task queue status."""
        return {
            'current_task': self.current_task,
            'task_queue': self.task_queue,
            'completed_tasks': self.completed_tasks[-10:],  # Last 10 completed
            'queue_length': len(self.task_queue),
            'completed_count': len(self.completed_tasks),
            'current_iteration': self.metrics.iterations,
            'task_duration': (time.time() - self.task_start_time) if self.task_start_time else None
        }
    
    def get_orchestrator_state(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator state."""
        return {
            'id': id(self),  # Unique instance ID
            'status': 'paused' if self.stop_requested else 'running',
            'primary_tool': self.primary_tool,
            'prompt_file': str(self.prompt_file),
            'iteration': self.metrics.iterations,
            'max_iterations': self.max_iterations,
            'runtime': time.time() - getattr(self, '_start_time', time.time()),
            'max_runtime': self.max_runtime,
            'tasks': self.get_task_status(),
            'metrics': {
                'successful': self.metrics.successful_iterations,
                'failed': self.metrics.failed_iterations,
                'errors': self.metrics.errors,
                'checkpoints': self.metrics.checkpoints,
                'rollbacks': self.metrics.rollbacks
            },
            'cost': {
                'total': self.cost_tracker.total_cost if self.cost_tracker else 0,
                'limit': self.max_cost if self.track_costs else None
            }
        }