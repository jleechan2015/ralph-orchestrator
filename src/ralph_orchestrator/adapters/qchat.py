# ABOUTME: Q Chat adapter implementation for q CLI tool
# ABOUTME: Provides integration with q chat command for AI interactions

"""Q Chat adapter for Ralph Orchestrator."""

import subprocess
import os
import sys
from typing import Optional
from .base import ToolAdapter, ToolResponse


class QChatAdapter(ToolAdapter):
    """Adapter for Q Chat CLI tool."""
    
    def __init__(self):
        self.command = "q"
        super().__init__("qchat")
    
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
            
            # Construct a more effective prompt for q chat
            # Tell it explicitly to edit the prompt file and add TASK_COMPLETE
            effective_prompt = (
                f"Please read and complete the task described in the file '{prompt_file}'. "
                f"The current content is:\n\n{prompt}\n\n"
                f"Edit the file '{prompt_file}' directly to add your solution. "
                f"When you have completed the task, add 'TASK_COMPLETE' on its own line at the end of the file."
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
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Collect output while streaming
            stdout_lines = []
            stderr_lines = []
            
            # Stream output in real-time
            import select
            import time
            
            timeout = kwargs.get("timeout", 600)  # Increase default to 10 minutes for complex tasks
            start_time = time.time()
            
            while True:
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
                
                # Use select to read available data without blocking
                # Use shorter timeout to be more responsive to process completion and timeouts
                remaining_timeout = max(0, timeout - elapsed_time)
                select_timeout = min(0.1, remaining_timeout)
                readable, _, _ = select.select([process.stdout, process.stderr], [], [], select_timeout)
                
                for stream in readable:
                    if stream == process.stdout:
                        line = stream.readline()
                        if line:
                            stdout_lines.append(line)
                            if verbose:
                                print(f"{line}", end='', file=sys.stderr)
                    elif stream == process.stderr:
                        line = stream.readline()
                        if line:
                            stderr_lines.append(line)
                            if verbose:
                                print(f"{line}", end='', file=sys.stderr)
            
            # Get final return code
            returncode = process.poll()
            
            if verbose:
                print("-" * 60, file=sys.stderr)
                print(f"Process completed with return code: {returncode}", file=sys.stderr)
                print(f"Total execution time: {time.time() - start_time:.2f} seconds", file=sys.stderr)
            
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
    
    def estimate_cost(self, prompt: str) -> float:
        """Q chat cost estimation (if applicable)."""
        # Q chat might be free or have different pricing
        # Return 0 for now, can be updated based on actual pricing
        return 0.0