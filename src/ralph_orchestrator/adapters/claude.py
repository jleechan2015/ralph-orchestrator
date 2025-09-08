# ABOUTME: Claude SDK adapter implementation
# ABOUTME: Provides integration with Anthropic's Claude via Python SDK

"""Claude SDK adapter for Ralph Orchestrator."""

import asyncio
import os
import logging
from typing import Optional, AsyncIterator
from pathlib import Path
from .base import ToolAdapter, ToolResponse

# Setup logging
logger = logging.getLogger(__name__)

try:
    from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, query
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False


class ClaudeAdapter(ToolAdapter):
    """Adapter for Claude using the Python SDK."""
    
    def __init__(self, verbose: bool = False):
        super().__init__("claude")
        self.sdk_available = CLAUDE_SDK_AVAILABLE
        self._system_prompt = None
        self._allowed_tools = None
        self._disallowed_tools = None
        self._enable_all_tools = False
        self.verbose = verbose
    
    def check_availability(self) -> bool:
        """Check if Claude SDK is available and properly configured."""
        # Claude Code SDK works without API key - it uses the local environment
        return CLAUDE_SDK_AVAILABLE
    
    def configure(self, 
                  system_prompt: Optional[str] = None,
                  allowed_tools: Optional[list] = None,
                  disallowed_tools: Optional[list] = None,
                  enable_all_tools: bool = False):
        """Configure the Claude adapter with custom options.
        
        Args:
            system_prompt: Custom system prompt for Claude
            allowed_tools: List of allowed tools for Claude to use (if None and enable_all_tools=True, all tools are enabled)
            disallowed_tools: List of disallowed tools
            enable_all_tools: If True and allowed_tools is None, enables all native Claude tools
        """
        self._system_prompt = system_prompt
        self._allowed_tools = allowed_tools
        self._disallowed_tools = disallowed_tools
        self._enable_all_tools = enable_all_tools
    
    def execute(self, prompt: str, **kwargs) -> ToolResponse:
        """Execute Claude with the given prompt synchronously.
        
        This is a blocking wrapper around the async implementation.
        """
        try:
            # Create new event loop if needed
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(self.aexecute(prompt, **kwargs))
            else:
                # If loop is already running, schedule as task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.aexecute(prompt, **kwargs))
                    return future.result()
        except Exception as e:
            return ToolResponse(
                success=False,
                output="",
                error=str(e)
            )
    
    async def aexecute(self, prompt: str, **kwargs) -> ToolResponse:
        """Execute Claude with the given prompt asynchronously."""
        if not self.available:
            logger.warning("Claude SDK not available")
            return ToolResponse(
                success=False,
                output="",
                error="Claude SDK is not available"
            )
        
        try:
            # Get configuration from kwargs or use defaults
            prompt_file = kwargs.get('prompt_file', 'PROMPT.md')
            timeout = kwargs.get("timeout", 300)
            
            # Build options for Claude Code
            options_dict = {}
            
            # Set system prompt
            system_prompt = kwargs.get('system_prompt', self._system_prompt)
            if not system_prompt:
                # Create a default system prompt for file editing
                system_prompt = (
                    f"You are helping complete a task. "
                    f"The task is described in the file '{prompt_file}'. "
                    f"Please edit this file directly to add your solution. "
                    f"When you have completed the task, add 'TASK_COMPLETE' on its own line at the end of the file."
                )
            options_dict['system_prompt'] = system_prompt
            
            # Set tool restrictions if provided
            # If enable_all_tools is True and no allowed_tools specified, don't set any restrictions
            enable_all_tools = kwargs.get('enable_all_tools', self._enable_all_tools)
            allowed_tools = kwargs.get('allowed_tools', self._allowed_tools)
            disallowed_tools = kwargs.get('disallowed_tools', self._disallowed_tools)
            
            # Only set tool restrictions if we're not enabling all tools or if specific tools are provided
            if not enable_all_tools or allowed_tools:
                if allowed_tools:
                    options_dict['allowed_tools'] = allowed_tools
                
                if disallowed_tools:
                    options_dict['disallowed_tools'] = disallowed_tools
            
            # If enable_all_tools is True and no allowed_tools, Claude will have access to all native tools
            if enable_all_tools and not allowed_tools:
                if self.verbose:
                    logger.info("Enabling all native Claude tools")
            
            # Create options
            options = ClaudeCodeOptions(**options_dict)
            
            # Log request details if verbose
            if self.verbose:
                logger.info(f"Claude SDK Request:")
                logger.info(f"  Prompt length: {len(prompt)} characters")
                logger.info(f"  System prompt: {system_prompt[:100]}..." if len(system_prompt) > 100 else f"  System prompt: {system_prompt}")
                if allowed_tools:
                    logger.info(f"  Allowed tools: {allowed_tools}")
                if disallowed_tools:
                    logger.info(f"  Disallowed tools: {disallowed_tools}")
            
            # Collect all response chunks
            output_chunks = []
            tokens_used = 0
            chunk_count = 0
            
            # Use one-shot query for simpler execution
            if self.verbose:
                logger.info("Starting Claude SDK query...")
                print("\n" + "="*50)
                print("CLAUDE PROCESSING:")
                print("="*50)
            
            async for message in query(prompt=prompt, options=options):
                chunk_count += 1
                msg_type = type(message).__name__
                
                if self.verbose:
                    print(f"\n[DEBUG: Received {msg_type}]", flush=True)
                    logger.debug(f"Received message type: {msg_type}")
                
                # Handle different message types
                if msg_type == 'AssistantMessage':
                    # Extract content from AssistantMessage
                    if hasattr(message, 'content') and message.content:
                        for content_block in message.content:
                            block_type = type(content_block).__name__
                            
                            if hasattr(content_block, 'text'):
                                # TextBlock
                                text = content_block.text
                                output_chunks.append(text)
                                
                                # Stream output to console in real-time when verbose
                                if self.verbose and text:
                                    print(text, end='', flush=True)
                                    logger.debug(f"Received assistant text: {len(text)} characters")
                            
                            elif block_type == 'ToolUseBlock':
                                # Tool use block - log but don't include in output
                                if self.verbose:
                                    tool_name = getattr(content_block, 'name', 'unknown')
                                    tool_id = getattr(content_block, 'id', 'unknown')
                                    print(f"\n[Tool: {tool_name}]", flush=True)
                                    logger.info(f"Tool use detected: {tool_name} (id: {tool_id[:8]}...)")
                                    if hasattr(content_block, 'input'):
                                        logger.debug(f"  Tool input: {content_block.input}")
                            
                            else:
                                if self.verbose:
                                    logger.debug(f"Unknown content block type: {block_type}")
                
                elif msg_type == 'ResultMessage':
                    # ResultMessage contains final result and usage stats
                    if hasattr(message, 'result'):
                        # Don't append result - it's usually a duplicate of assistant message
                        if self.verbose:
                            logger.debug(f"Result message received: {len(str(message.result))} characters")
                    
                    # Extract token usage from ResultMessage
                    if hasattr(message, 'usage'):
                        usage = message.usage
                        if isinstance(usage, dict):
                            tokens_used = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                        else:
                            tokens_used = getattr(usage, 'total_tokens', 0)
                        if self.verbose:
                            logger.debug(f"Token usage: {tokens_used} tokens")
                
                elif msg_type == 'SystemMessage':
                    # SystemMessage is initialization data, skip it
                    if self.verbose:
                        logger.debug("System initialization message received")
                
                elif msg_type == 'UserMessage':
                    # User message (tool results being sent back)
                    if self.verbose:
                        logger.debug("User message (tool result) received")
                
                elif msg_type == 'ToolResultMessage':
                    # Tool result message
                    if self.verbose:
                        logger.debug("Tool result message received")
                
                elif hasattr(message, 'text'):
                    # Generic text message
                    chunk_text = message.text
                    output_chunks.append(chunk_text)
                    if self.verbose:
                        print(chunk_text, end='', flush=True)
                        logger.debug(f"Received text chunk {chunk_count}: {len(chunk_text)} characters")
                
                elif isinstance(message, str):
                    # Plain string message
                    output_chunks.append(message)
                    if self.verbose:
                        print(message, end='', flush=True)
                        logger.debug(f"Received string chunk {chunk_count}: {len(message)} characters")
                
                else:
                    if self.verbose:
                        logger.debug(f"Unknown message type {msg_type}: {message}")
            
            # Combine output
            output = ''.join(output_chunks)
            
            # End streaming section if verbose
            if self.verbose:
                print("\n" + "="*50 + "\n")
            
            # Always log the output we're about to return
            logger.info(f"Claude adapter returning {len(output)} characters of output")
            if output:
                logger.debug(f"Output preview: {output[:200]}...")
            
            # Calculate cost if we have token count
            cost = self._calculate_cost(tokens_used) if tokens_used > 0 else None
            
            # Log response details if verbose
            if self.verbose:
                logger.info(f"Claude SDK Response:")
                logger.info(f"  Output length: {len(output)} characters")
                logger.info(f"  Chunks received: {chunk_count}")
                if tokens_used > 0:
                    logger.info(f"  Tokens used: {tokens_used}")
                    if cost:
                        logger.info(f"  Estimated cost: ${cost:.4f}")
                logger.debug(f"Response preview: {output[:500]}..." if len(output) > 500 else f"Response: {output}")
            
            return ToolResponse(
                success=True,
                output=output,
                tokens_used=tokens_used if tokens_used > 0 else None,
                cost=cost,
                metadata={"model": kwargs.get("model", "claude-3-sonnet")}
            )
            
        except asyncio.TimeoutError:
            logger.error("Claude SDK request timed out")
            return ToolResponse(
                success=False,
                output="",
                error="Claude SDK request timed out"
            )
        except Exception as e:
            logger.error(f"Claude SDK error: {str(e)}", exc_info=True)
            return ToolResponse(
                success=False,
                output="",
                error=str(e)
            )
    
    def _calculate_cost(self, tokens: Optional[int]) -> Optional[float]:
        """Calculate estimated cost based on tokens."""
        if not tokens:
            return None
        
        # Claude 3 Sonnet pricing (approximate)
        # $0.003 per 1K input tokens, $0.015 per 1K output tokens
        # Using average for estimation
        cost_per_1k = 0.009
        return (tokens / 1000) * cost_per_1k
    
    def estimate_cost(self, prompt: str) -> float:
        """Estimate cost for the prompt."""
        # Rough estimation: 1 token ≈ 4 characters
        estimated_tokens = len(prompt) / 4
        return self._calculate_cost(estimated_tokens) or 0.0