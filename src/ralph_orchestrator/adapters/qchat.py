# ABOUTME: Q Chat adapter implementation for q CLI tool
# ABOUTME: Provides integration with q chat command for AI interactions

"""Q Chat adapter for Ralph Orchestrator."""

import subprocess
import os
import sys
import signal
import threading
import asyncio
import select
import time
import fcntl
from typing import Optional, Dict, Any
from contextlib import contextmanager
from .base import ToolAdapter, ToolResponse


class QChatAdapter(ToolAdapter):
    """Adapter for Q Chat CLI tool."""
    
    def __init__(self):
        self.command = "q"
        super().__init__("qchat")
        self.current_process = None
        self.shutdown_requested = False
        
        # Thread synchronization
        self._lock = threading.Lock()
        
        # Store original signal handlers for cleanup
        self._original_sigint = None
        self._original_sigterm = None
        
        # Register signal handlers to propagate shutdown to subprocess
        self._register_signal_handlers()
    
    def _register_signal_handlers(self):
        """Register signal handlers and store originals."""
        self._original_sigint = signal.signal(signal.SIGINT, self._signal_handler)
        self._original_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _restore_signal_handlers(self):
        """Restore original signal handlers."""
        if self._original_sigint is not None:
            signal.signal(signal.SIGINT, self._original_sigint)
        if self._original_sigterm is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals and terminate running subprocess."""
        with self._lock:
            self.shutdown_requested = True
            process = self.current_process
        
        if process and process.poll() is None:
            print(f"\nReceived signal {signum}, terminating q chat process...", file=sys.stderr)
            try:
                process.terminate()
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print("Force killing q chat process...", file=sys.stderr)
                process.kill()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
    
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
            # Get verbose flag from kwargs
            verbose = kwargs.get('verbose', True)
            
            # Get the prompt file path from kwargs if available
            prompt_file = kwargs.get('prompt_file', 'PROMPT.md')
            
            # Enhance prompt with orchestration instructions
            enhanced_prompt = self._enhance_prompt_with_instructions(prompt)
            
            # Construct a more effective prompt for q chat
            # Tell it explicitly to edit the prompt file
            effective_prompt = (
                f"Please read and complete the task described in the file '{prompt_file}'. "
                f"The current content is:\n\n{enhanced_prompt}\n\n"
                f"Edit the file '{prompt_file}' directly to add your solution and progress updates."
            )
            
            # Build command - q chat works with files by adding them to context
            # We pass the prompt through stdin and tell it to trust file operations
            cmd = [
                self.command, 
                "chat",
                "--no-interactive",  # Don't expect user input
                "--trust-all-tools",  # Allow all tool operations
                effective_prompt  # Pass the enhanced prompt
            ]
            
            if verbose:
                print(f"Starting q chat command...", file=sys.stderr)
                print(f"Command: {' '.join(cmd)}", file=sys.stderr)
                print(f"Working directory: {os.getcwd()}", file=sys.stderr)
                print(f"Timeout: {kwargs.get('timeout', 300)} seconds", file=sys.stderr)
                print("-" * 60, file=sys.stderr)
            
            # Use Popen for real-time output streaming
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd(),
                bufsize=0,  # Unbuffered to prevent deadlock
                universal_newlines=True
            )
            
            # Set process reference with lock
            with self._lock:
                self.current_process = process
            
            # Make pipes non-blocking to prevent deadlock
            self._make_non_blocking(process.stdout)
            self._make_non_blocking(process.stderr)
            
            # Collect output while streaming
            stdout_lines = []
            stderr_lines = []
            
            timeout = kwargs.get("timeout", 600)  # Increase default to 10 minutes for complex tasks
            start_time = time.time()
            
            while True:
                # Check for shutdown signal first with lock
                with self._lock:
                    shutdown = self.shutdown_requested
                
                if shutdown:
                    if verbose:
                        print("Shutdown requested, terminating q chat process...", file=sys.stderr)
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=2)
                    
                    # Clean up process reference with lock
                    with self._lock:
                        self.current_process = None
                    
                    return ToolResponse(
                        success=False,
                        output="".join(stdout_lines),
                        error="Process terminated due to shutdown signal"
                    )
                
                # Check for timeout
                elapsed_time = time.time() - start_time
                
                # Log progress every 30 seconds when verbose
                if verbose and int(elapsed_time) % 30 == 0 and int(elapsed_time) > 0:
                    print(f"Q chat still running... elapsed: {elapsed_time:.1f}s / {timeout}s", file=sys.stderr)
                    # Also check if the process seems stuck (no output for a while)
                    if len(stdout_lines) == 0 and len(stderr_lines) == 0 and elapsed_time > 60:
                        print("Warning: No output received yet, Q might be stuck", file=sys.stderr)
                
                if elapsed_time > timeout:
                    if verbose:
                        print(f"Command timed out after {elapsed_time:.2f} seconds", file=sys.stderr)
                    
                    # Try to terminate gracefully first
                    process.terminate()
                    try:
                        # Wait a bit for graceful termination
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        if verbose:
                            print("Graceful termination failed, force killing process", file=sys.stderr)
                        process.kill()
                        # Wait for force kill to complete
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            if verbose:
                                print("Warning: Process may still be running after kill", file=sys.stderr)
                    
                    # Try to capture any remaining output after termination
                    try:
                        remaining_stdout = process.stdout.read()
                        remaining_stderr = process.stderr.read()
                        if remaining_stdout:
                            stdout_lines.append(remaining_stdout)
                        if remaining_stderr:
                            stderr_lines.append(remaining_stderr)
                    except Exception as e:
                        if verbose:
                            print(f"Warning: Could not read remaining output after timeout: {e}", file=sys.stderr)
                    
                    # Clean up process reference with lock
                    with self._lock:
                        self.current_process = None
                    
                    return ToolResponse(
                        success=False,
                        output="".join(stdout_lines),
                        error=f"q chat command timed out after {elapsed_time:.2f} seconds"
                    )
                
                # Check if process is still running
                if process.poll() is not None:
                    # Process finished, read remaining output
                    remaining_stdout = process.stdout.read()
                    remaining_stderr = process.stderr.read()
                    
                    if remaining_stdout:
                        stdout_lines.append(remaining_stdout)
                        if verbose:
                            print(f"{remaining_stdout}", end='', file=sys.stderr)
                    
                    if remaining_stderr:
                        stderr_lines.append(remaining_stderr)
                        if verbose:
                            print(f"{remaining_stderr}", end='', file=sys.stderr)
                    
                    break
                
                # Read available data without blocking
                try:
                    # Read stdout
                    stdout_data = self._read_available(process.stdout)
                    if stdout_data:
                        stdout_lines.append(stdout_data)
                        if verbose:
                            print(stdout_data, end='', file=sys.stderr)
                    
                    # Read stderr
                    stderr_data = self._read_available(process.stderr)
                    if stderr_data:
                        stderr_lines.append(stderr_data)
                        if verbose:
                            print(stderr_data, end='', file=sys.stderr)
                    
                    # Small sleep to prevent busy waiting
                    time.sleep(0.01)
                    
                except IOError:
                    # Non-blocking read, ignore would-block errors
                    pass
            
            # Get final return code
            returncode = process.poll()
            
            if verbose:
                print("-" * 60, file=sys.stderr)
                print(f"Process completed with return code: {returncode}", file=sys.stderr)
                print(f"Total execution time: {time.time() - start_time:.2f} seconds", file=sys.stderr)
            
            # Clean up process reference with lock
            with self._lock:
                self.current_process = None
            
            # Combine output
            full_stdout = "".join(stdout_lines)
            full_stderr = "".join(stderr_lines)
            
            if returncode == 0:
                return ToolResponse(
                    success=True,
                    output=full_stdout,
                    metadata={
                        "tool": "q chat",
                        "execution_time": time.time() - start_time,
                        "verbose": verbose
                    }
                )
            else:
                return ToolResponse(
                    success=False,
                    output=full_stdout,
                    error=full_stderr or "q chat command failed"
                )
                
        except Exception as e:
            if verbose:
                print(f"Exception occurred: {str(e)}", file=sys.stderr)
            return ToolResponse(
                success=False,
                output="",
                error=str(e)
            )
    
    def _make_non_blocking(self, pipe):
        """Make a pipe non-blocking to prevent deadlock."""
        if pipe:
            try:
                fd = pipe.fileno()
                # Check if fd is a valid integer file descriptor
                if isinstance(fd, int) and fd >= 0:
                    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            except (AttributeError, ValueError, OSError):
                # In tests or when pipe doesn't support fileno()
                pass
    
    def _read_available(self, pipe):
        """Read available data from a non-blocking pipe."""
        if not pipe:
            return ""
        
        try:
            # Try to read up to 4KB at a time
            data = pipe.read(4096)
            # Ensure we always return a string, not None
            if data is None:
                return ""
            return data if data else ""
        except (IOError, OSError):
            # Would block or no data available
            return ""
    
    async def aexecute(self, prompt: str, **kwargs) -> ToolResponse:
        """Native async execution using asyncio subprocess."""
        if not self.available:
            return ToolResponse(
                success=False,
                output="",
                error="q CLI is not available"
            )
        
        try:
            verbose = kwargs.get('verbose', True)
            prompt_file = kwargs.get('prompt_file', 'PROMPT.md')
            timeout = kwargs.get('timeout', 600)
            
            # Enhance prompt with orchestration instructions
            enhanced_prompt = self._enhance_prompt_with_instructions(prompt)
            
            # Construct effective prompt
            effective_prompt = (
                f"Please read and complete the task described in the file '{prompt_file}'. "
                f"The current content is:\n\n{enhanced_prompt}\n\n"
                f"Edit the file '{prompt_file}' directly to add your solution and progress updates."
            )
            
            # Build command
            cmd = [
                self.command,
                "chat",
                "--no-interactive",
                "--trust-all-tools",
                effective_prompt
            ]
            
            if verbose:
                print(f"Starting q chat command (async)...", file=sys.stderr)
                print(f"Command: {' '.join(cmd)}", file=sys.stderr)
                print("-" * 60, file=sys.stderr)
            
            # Create async subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Set process reference with lock
            with self._lock:
                self.current_process = process
            
            try:
                # Wait for completion with timeout
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                # Decode output
                stdout = stdout_data.decode('utf-8') if stdout_data else ""
                stderr = stderr_data.decode('utf-8') if stderr_data else ""
                
                if verbose and stdout:
                    print(stdout, file=sys.stderr)
                if verbose and stderr:
                    print(stderr, file=sys.stderr)
                
                # Check return code
                if process.returncode == 0:
                    return ToolResponse(
                        success=True,
                        output=stdout,
                        metadata={
                            "tool": "q chat",
                            "verbose": verbose,
                            "async": True
                        }
                    )
                else:
                    return ToolResponse(
                        success=False,
                        output=stdout,
                        error=stderr or f"q chat failed with code {process.returncode}"
                    )
                
            except asyncio.TimeoutError:
                # Timeout occurred
                if verbose:
                    print(f"Async q chat timed out after {timeout} seconds", file=sys.stderr)
                
                # Try to terminate process
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=3)
                except (asyncio.TimeoutError, ProcessLookupError):
                    try:
                        process.kill()
                        await process.wait()
                    except ProcessLookupError:
                        pass
                
                return ToolResponse(
                    success=False,
                    output="",
                    error=f"q chat command timed out after {timeout} seconds"
                )
            
            finally:
                # Clean up process reference
                with self._lock:
                    self.current_process = None
                    
        except Exception as e:
            if kwargs.get('verbose'):
                print(f"Async execution error: {str(e)}", file=sys.stderr)
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
    
    def __del__(self):
        """Cleanup on deletion."""
        # Restore original signal handlers
        self._restore_signal_handlers()
        
        # Ensure any running process is terminated
        with self._lock:
            process = self.current_process
        
        if process:
            try:
                if hasattr(process, 'poll'):
                    # Sync process
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=1)
                else:
                    # Async process - can't do much in __del__
                    pass
            except:
                pass