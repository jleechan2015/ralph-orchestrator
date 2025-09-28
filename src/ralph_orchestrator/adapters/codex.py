# ABOUTME: Codex adapter implementation for Ralph Orchestrator
# ABOUTME: Provides integration with Codex CLI tool

"""Codex adapter for Ralph Orchestrator."""

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from .base import ToolAdapter, ToolResponse

# Setup logging
logger = logging.getLogger(__name__)


class CodexAdapter(ToolAdapter):
    """Adapter for Codex CLI tool."""

    def __init__(self, verbose: bool = False):
        super().__init__("codex")
        self._verbose = verbose

    def check_availability(self) -> bool:
        """Check if codex CLI is available."""
        try:
            result = subprocess.run(
                ["codex", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False

    def execute(self, prompt: str, **kwargs) -> ToolResponse:
        """Execute prompt using codex CLI."""
        try:
            # Create temporary file for prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name

            try:
                # Build codex command
                cmd = ["codex", "exec", "--yolo"]

                if self._verbose:
                    cmd.extend(["-c", "verbose=true"])

                # Add debug mode for better error reporting
                cmd.extend(["-c", "debug=true"])

                # Execute codex command with prompt from stdin
                with open(prompt_file, 'r') as f:
                    result = subprocess.run(
                        cmd,
                        stdin=f,
                        capture_output=True,
                        text=True,
                        timeout=3600  # 1 hour timeout
                    )

                success = result.returncode == 0
                output = result.stdout if success else result.stderr

                if self._verbose:
                    logger.info(f"Codex execution {'succeeded' if success else 'failed'}")
                    if not success:
                        logger.error(f"Codex error: {result.stderr}")

                return ToolResponse(
                    success=success,
                    output=output,
                    error=result.stderr if not success else None,
                    metadata={
                        "command": " ".join(cmd),
                        "return_code": result.returncode,
                        "execution_time": None  # Could add timing if needed
                    }
                )

            finally:
                # Clean up temporary file
                Path(prompt_file).unlink(missing_ok=True)

        except subprocess.TimeoutExpired:
            error_msg = "Codex execution timed out"
            logger.error(error_msg)
            return ToolResponse(
                success=False,
                output="",
                error=error_msg,
                metadata={"timeout": True}
            )

        except Exception as e:
            error_msg = f"Codex execution failed: {str(e)}"
            logger.error(error_msg)
            return ToolResponse(
                success=False,
                output="",
                error=error_msg,
                metadata={"exception": str(e)}
            )

    async def execute_async(self, prompt: str, **kwargs) -> ToolResponse:
        """Async version of execute."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, prompt)