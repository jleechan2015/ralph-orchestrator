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
import hashlib
import platform
import re
import shlex
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Optional monitoring dependencies
try:
    import psutil
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

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

@dataclass
class TokenMetrics:
    """Token usage and cost tracking"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0
    iterations: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_iteration(self, input_tokens: int, output_tokens: int, agent_type: str):
        """Add token usage for an iteration"""
        costs = TOKEN_COSTS.get(agent_type, {"input": 1.0, "output": 3.0})
        iteration_cost = (input_tokens * costs["input"] / 1_000_000 + 
                         output_tokens * costs["output"] / 1_000_000)
        
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_cost += iteration_cost
        
        self.iterations.append({
            "timestamp": datetime.now().isoformat(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": iteration_cost,
            "cumulative_cost": self.total_cost
        })
    
    def get_total_tokens(self) -> int:
        """Get total token count"""
        return self.input_tokens + self.output_tokens
    
    def is_within_limits(self, max_tokens: int, max_cost: float) -> bool:
        """Check if within token and cost limits"""
        return self.get_total_tokens() < max_tokens and self.total_cost < max_cost

class ContextManager:
    """Manages context window and prompt summarization"""
    
    def __init__(self, window_size: int, threshold: float):
        self.window_size = window_size
        self.threshold = threshold
        self.prompt_history = []
        self.summary_cache = {}
        
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text"""
        return len(text) // 4
    
    def add_to_history(self, prompt_path: Path):
        """Add prompt to history and track size"""
        content = prompt_path.read_text()
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        self.prompt_history.append({
            'path': str(prompt_path),
            'content': content,
            'hash': content_hash,
            'tokens': self.estimate_tokens(content),
            'timestamp': datetime.now().isoformat()
        })
    
    def needs_summarization(self, current_prompt: str) -> bool:
        """Check if context needs summarization"""
        current_tokens = self.estimate_tokens(current_prompt)
        threshold_tokens = int(self.window_size * self.threshold)
        return current_tokens > threshold_tokens
    
    def summarize_prompt(self, prompt_path: Path) -> Tuple[bool, Optional[Path]]:
        """Summarize prompt if needed, returns (was_summarized, new_path)"""
        content = prompt_path.read_text()
        
        if not self.needs_summarization(content):
            return False, None
            
        logger.info(f"Context approaching limit, creating summary...")
        
        # Create summary prompt for the agent
        summary_prompt = f"""CONTEXT OVERFLOW DETECTED

The following prompt has grown too large. Please create a concise summary that preserves:
1. The original task/goal
2. Key completed steps
3. Current state and next actions
4. Critical context and constraints

ORIGINAL PROMPT:
{content}

Please write a new, shorter prompt that continues the task.
Mark the end with: TASK_COMPLETE if done, or continue normally.
"""
        
        # Save summary prompt
        summary_path = Path(f".agent/prompts/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        summary_path.write_text(summary_prompt)
        
        return True, summary_path

class MetricsCollector:
    """Collects and reports system and application metrics"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and METRICS_AVAILABLE
        self.metrics_history = []
        self.start_time = time.time()
        
        if enabled and not METRICS_AVAILABLE:
            logger.warning("Metrics requested but psutil not installed. Run: pip install psutil")
        
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        if not self.enabled:
            return {}
            
        try:
            import psutil
            process = psutil.Process()
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory': {
                    'percent': psutil.virtual_memory().percent,
                    'used_gb': psutil.virtual_memory().used / (1024**3),
                    'available_gb': psutil.virtual_memory().available / (1024**3)
                },
                'process': {
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': process.memory_info().rss / (1024**2),
                    'num_threads': process.num_threads()
                },
                'disk': {
                    'usage_percent': psutil.disk_usage('/').percent,
                    'free_gb': psutil.disk_usage('/').free / (1024**3)
                }
            }
        except Exception as e:
            logger.debug(f"Failed to collect system metrics: {e}")
            return {}
    
    def record_iteration_metrics(self, iteration: int, duration: float, 
                                tokens: int, cost: float, success: bool):
        """Record metrics for an iteration"""
        if not self.enabled:
            return
            
        metrics = {
            'iteration': iteration,
            'duration_seconds': duration,
            'tokens_used': tokens,
            'cost_usd': cost,
            'success': success,
            'system': self.collect_system_metrics(),
            'uptime_seconds': time.time() - self.start_time
        }
        
        self.metrics_history.append(metrics)
        
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        if not self.metrics_history:
            return {}
            
        total_iterations = len(self.metrics_history)
        successful = sum(1 for m in self.metrics_history if m.get('success', False))
        
        summary = {
            'total_iterations': total_iterations,
            'successful_iterations': successful,
            'success_rate': successful / total_iterations if total_iterations > 0 else 0,
            'total_duration_seconds': sum(m['duration_seconds'] for m in self.metrics_history),
            'average_duration_seconds': sum(m['duration_seconds'] for m in self.metrics_history) / total_iterations,
            'total_tokens': sum(m['tokens_used'] for m in self.metrics_history),
            'total_cost_usd': sum(m['cost_usd'] for m in self.metrics_history),
            'system_info': {
                'platform': platform.platform(),
                'python_version': platform.python_version()
            }
        }
        
        if METRICS_AVAILABLE:
            import psutil
            summary['system_info']['cpu_count'] = psutil.cpu_count()
            
        return summary
    
    def save_metrics(self, path: Path):
        """Save metrics to file"""
        if not self.enabled or not self.metrics_history:
            return
            
        metrics_data = {
            'summary': self.get_summary(),
            'history': self.metrics_history
        }
        
        path.write_text(json.dumps(metrics_data, indent=2))
        logger.debug(f"Saved metrics to {path}")

class SecurityValidator:
    """Validates and sanitizes inputs for security"""
    
    # Patterns that might indicate malicious content
    UNSAFE_PATTERNS = [
        r'\$\(.*\)',  # Command substitution
        r'`.*`',       # Backtick command substitution
        r'\|\s*sh',   # Pipe to shell
        r'\|\s*bash', # Pipe to bash
        r'&&\s*rm',   # Chained rm command
        r';\s*rm',    # Semicolon rm command
        r'\.\./',     # Directory traversal
        r'~/',        # Home directory access (configurable)
    ]
    
    # File extensions that should not be used as prompts
    FORBIDDEN_EXTENSIONS = {'.exe', '.dll', '.so', '.dylib', '.bin', '.app'}
    
    @classmethod
    def validate_prompt_file(cls, path: Path, max_size: int, allow_unsafe: bool = False) -> Tuple[bool, Optional[str]]:
        """Validate prompt file for security issues"""
        
        # Check file exists
        if not path.exists():
            return False, f"File not found: {path}"
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > max_size:
            return False, f"File too large: {file_size} bytes (max: {max_size})"
        
        # Check file extension
        if path.suffix.lower() in cls.FORBIDDEN_EXTENSIONS:
            return False, f"Forbidden file type: {path.suffix}"
        
        # Check for directory traversal
        try:
            resolved = path.resolve()
            if not allow_unsafe and '..' in str(path):
                return False, "Path contains directory traversal"
        except Exception as e:
            return False, f"Invalid path: {e}"
        
        # Check file content for unsafe patterns
        if not allow_unsafe:
            try:
                content = path.read_text(errors='ignore')
                for pattern in cls.UNSAFE_PATTERNS:
                    if re.search(pattern, content, re.IGNORECASE):
                        return False, f"Potentially unsafe content detected: {pattern}"
            except Exception as e:
                return False, f"Cannot read file: {e}"
        
        return True, None
    
    @classmethod
    def sanitize_command_args(cls, args: List[str]) -> List[str]:
        """Sanitize command arguments for shell execution"""
        sanitized = []
        for arg in args:
            # Use shlex.quote for proper shell escaping
            sanitized.append(shlex.quote(arg))
        return sanitized
    
    @classmethod
    def validate_agent_command(cls, cmd: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate agent command for safety"""
        if not cmd:
            return False, "Empty command"
        
        # Check for shell injection attempts in command
        dangerous_chars = ['$', '`', ';', '&&', '||', '>', '<', '|']
        for part in cmd:
            for char in dangerous_chars:
                if char in part and not part.startswith('--'):
                    return False, f"Potentially dangerous character in command: {char}"
        
        return True, None

class RalphOrchestrator:
    """Main orchestrator for Ralph Wiggum technique"""
    
    def __init__(self, config: RalphConfig):
        self.config = config
        self.iteration_count = 0
        self.start_time = time.time()
        self.errors = []
        self.checkpoints = []
        self.token_metrics = TokenMetrics()
        self.current_agent = None
        self.context_manager = ContextManager(
            config.context_window,
            config.context_threshold
        )
        self.metrics_collector = MetricsCollector(config.enable_metrics)
        self.iteration_start_time = None
        self.security_validator = SecurityValidator()
        self.setup_signal_handlers()
        self.setup_directories()
        
        # Validate initial prompt file
        self._validate_prompt_security()
        
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
    
    def _validate_prompt_security(self):
        """Validate prompt file security on startup"""
        prompt_path = Path(self.config.prompt_file)
        is_valid, error = self.security_validator.validate_prompt_file(
            prompt_path, 
            self.config.max_prompt_size,
            self.config.allow_unsafe_paths
        )
        
        if not is_valid:
            logger.error(f"Security validation failed: {error}")
            if not self.config.allow_unsafe_paths:
                raise SecurityError(f"Prompt file failed security validation: {error}")
            
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
        
        self.current_agent = agent.value
            
        prompt_file = Path(self.config.prompt_file)
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        # Validate prompt file before use
        is_valid, error = self.security_validator.validate_prompt_file(
            prompt_file,
            self.config.max_prompt_size,
            self.config.allow_unsafe_paths
        )
        
        if not is_valid:
            raise SecurityError(f"Prompt validation failed: {error}")
            
        if agent == AgentType.CLAUDE:
            cmd = ["claude", "-p", f"@{prompt_file}"]
        elif agent == AgentType.Q:
            # Q chat reads the prompt as input text
            prompt_content = prompt_file.read_text()
            cmd = ["q", "chat", "--no-interactive", "--trust-all-tools", prompt_content]
        elif agent == AgentType.GEMINI:
            cmd = ["gemini", "-p", f"@{prompt_file}"]
        else:
            raise ValueError(f"Unsupported agent type: {agent}")
            
        # Sanitize and add additional agent arguments
        if self.config.agent_args:
            sanitized_args = self.security_validator.sanitize_command_args(self.config.agent_args)
            cmd.extend(sanitized_args)
        
        # Final command validation
        is_valid, error = self.security_validator.validate_agent_command(cmd)
        if not is_valid:
            raise SecurityError(f"Command validation failed: {error}")
        
        return cmd
        
    def check_completion(self) -> bool:
        """Check if task is marked as complete"""
        prompt_file = Path(self.config.prompt_file)
        if prompt_file.exists():
            content = prompt_file.read_text()
            return "TASK_COMPLETE" in content
        return False
        
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text (rough approximation)"""
        # Rough estimate: 1 token per 4 characters
        return len(text) // 4
    
    def run_iteration(self) -> bool:
        """Run a single iteration of the Ralph loop"""
        self.iteration_count += 1
        self.iteration_start_time = time.time()
        
        # Check token and cost limits before running
        if not self.token_metrics.is_within_limits(self.config.max_tokens, self.config.max_cost):
            logger.error(f"Token/cost limits exceeded: {self.token_metrics.get_total_tokens()} tokens, ${self.token_metrics.total_cost:.2f}")
            return True  # Stop gracefully
        
        logger.info(f"Iteration {self.iteration_count} starting...")
        logger.info(f"Current usage: {self.token_metrics.get_total_tokens()} tokens, ${self.token_metrics.total_cost:.2f}")
        
        # Check and handle context overflow
        prompt_path = Path(self.config.prompt_file)
        was_summarized, summary_path = self.context_manager.summarize_prompt(prompt_path)
        
        if was_summarized:
            logger.info(f"Created context summary at {summary_path}")
            # Temporarily use summary prompt
            original_prompt = self.config.prompt_file
            self.config.prompt_file = str(summary_path)
        
        try:
            cmd = self.build_agent_command()
            
            # Restore original prompt if summarized
            if was_summarized:
                self.config.prompt_file = original_prompt
            
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
            
            # Estimate token usage from input/output
            prompt_content = Path(self.config.prompt_file).read_text()
            input_tokens = self.estimate_tokens(prompt_content)
            output_tokens = self.estimate_tokens(result.stdout + result.stderr)
            
            # Track token usage and context
            self.token_metrics.add_iteration(input_tokens, output_tokens, self.current_agent)
            self.context_manager.add_to_history(Path(self.config.prompt_file))
            
            # Record metrics
            iteration_duration = time.time() - self.iteration_start_time
            iteration_tokens = input_tokens + output_tokens
            iteration_cost = self.token_metrics.iterations[-1]['cost'] if self.token_metrics.iterations else 0
            self.metrics_collector.record_iteration_metrics(
                self.iteration_count, iteration_duration, iteration_tokens, 
                iteration_cost, result.returncode == 0
            )
            
            # Log metrics periodically
            if self.iteration_count % self.config.metrics_interval == 0:
                self.log_metrics()
            
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
            'token_metrics': {
                'input_tokens': self.token_metrics.input_tokens,
                'output_tokens': self.token_metrics.output_tokens,
                'total_cost': self.token_metrics.total_cost,
                'total_tokens': self.token_metrics.get_total_tokens(),
                'iterations': self.token_metrics.iterations
            },
            'metrics_summary': self.metrics_collector.get_summary(),
            'config': {
                'agent': self.config.agent.value,
                'prompt_file': self.config.prompt_file,
                'max_iterations': self.config.max_iterations,
                'max_runtime': self.config.max_runtime,
                'max_tokens': self.config.max_tokens,
                'max_cost': self.config.max_cost,
                'context_window': self.config.context_window
            }
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        state_file = Path(f".agent/metrics/state_{timestamp}.json")
        state_file.write_text(json.dumps(state, indent=2))
        logger.info(f"Saved state to {state_file}")
        
        # Save detailed metrics
        metrics_file = Path(f".agent/metrics/metrics_{timestamp}.json")
        self.metrics_collector.save_metrics(metrics_file)
        
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
            
        # Check token and cost limits
        if not self.token_metrics.is_within_limits(self.config.max_tokens, self.config.max_cost):
            logger.warning(f"Approaching token/cost limits: {self.token_metrics.get_total_tokens()}/{self.config.max_tokens} tokens, ${self.token_metrics.total_cost:.2f}/${self.config.max_cost:.2f}")
            return False
            
        # Check for too many consecutive errors
        recent_errors = [e for e in self.errors if e['iteration'] > self.iteration_count - 5]
        if len(recent_errors) >= 5:
            logger.error("Too many consecutive errors, stopping")
            return False
            
        return True
    
    def log_metrics(self):
        """Log current metrics summary"""
        summary = self.metrics_collector.get_summary()
        if summary:
            logger.info(f"Metrics: {summary['successful_iterations']}/{summary['total_iterations']} successful, "
                       f"avg {summary['average_duration_seconds']:.1f}s/iteration, "
                       f"${summary['total_cost_usd']:.2f} total cost")
            
            # Log system metrics
            current_metrics = self.metrics_collector.collect_system_metrics()
            if current_metrics:
                logger.debug(f"System: CPU {current_metrics['cpu_percent']:.1f}%, "
                           f"Memory {current_metrics['memory']['percent']:.1f}%")
        
    def run(self):
        """Main orchestration loop"""
        logger.info(f"Starting Ralph orchestrator with {self.config.agent.value} agent")
        logger.info(f"Prompt file: {self.config.prompt_file}")
        logger.info(f"Max iterations: {self.config.max_iterations}")
        logger.info(f"Max runtime: {self.config.max_runtime}s")
        logger.info(f"Max tokens: {self.config.max_tokens:,}")
        logger.info(f"Max cost: ${self.config.max_cost:.2f}")
        logger.info(f"Context window: {self.config.context_window:,} tokens")
        if self.config.enable_metrics:
            logger.info(f"Metrics collection enabled (interval: {self.config.metrics_interval})")
        
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
        logger.info(f"Final usage: {self.token_metrics.get_total_tokens():,} tokens, ${self.token_metrics.total_cost:.2f}")
        
        # Log final metrics
        summary = self.metrics_collector.get_summary()
        if summary:
            logger.info(f"Final metrics: {summary['successful_iterations']}/{summary['total_iterations']} iterations succeeded")
            logger.info(f"Total runtime: {summary['total_duration_seconds']:.1f}s")
        
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
        help=f"Context summarization threshold (default: {DEFAULT_CONTEXT_THRESHOLD:.1%})"
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