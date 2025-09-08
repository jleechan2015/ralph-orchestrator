# ABOUTME: Claude SDK adapter implementation
# ABOUTME: Provides integration with Anthropic's Claude via Python SDK

"""Claude SDK adapter for Ralph Orchestrator."""

import asyncio
import logging
from typing import Optional
from .base import ToolAdapter, ToolResponse

# Setup logging
logger = logging.getLogger(__name__)

try:
    from claude_code_sdk import ClaudeCodeOptions, query
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
        self._enable_web_search = True  # Enable WebSearch by default
        self.verbose = verbose
    
    def check_availability(self) -> bool:
        """Check if Claude SDK is available and properly configured."""
        # Claude Code SDK works without API key - it uses the local environment
        return CLAUDE_SDK_AVAILABLE
    
    def configure(self, 
                  system_prompt: Optional[str] = None,
                  allowed_tools: Optional[list] = None,
                  disallowed_tools: Optional[list] = None,
                  enable_all_tools: bool = False,
                  enable_web_search: bool = True):
        """Configure the Claude adapter with custom options.
        
        Args:
            system_prompt: Custom system prompt for Claude
            allowed_tools: List of allowed tools for Claude to use (if None and enable_all_tools=True, all tools are enabled)
            disallowed_tools: List of disallowed tools
            enable_all_tools: If True and allowed_tools is None, enables all native Claude tools
            enable_web_search: If True, explicitly enables WebSearch tool (default: True)
        """
        self._system_prompt = system_prompt
        self._allowed_tools = allowed_tools
        self._disallowed_tools = disallowed_tools
        self._enable_all_tools = enable_all_tools
        self._enable_web_search = enable_web_search
        
        # If web search is enabled and we have an allowed tools list, add WebSearch to it
        if enable_web_search and allowed_tools is not None and 'WebSearch' not in allowed_tools:
            self._allowed_tools = allowed_tools + ['WebSearch']
    
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
            
            # Build options for Claude Code
            options_dict = {}
            
            # Set system prompt with orchestration context
            system_prompt = kwargs.get('system_prompt', self._system_prompt)
            if not system_prompt:
                # Create a default system prompt with orchestration context
                enhanced_prompt = self._enhance_prompt_with_instructions(prompt)
                system_prompt = (
                    f"You are helping complete a task. "
                    f"The task is described in the file '{prompt_file}'. "
                    f"Please edit this file directly to add your solution and progress updates."
                )
                # Use the enhanced prompt as the main prompt
                prompt = enhanced_prompt
            else:
                # If custom system prompt provided, still enhance the main prompt
                prompt = self._enhance_prompt_with_instructions(prompt)
            options_dict['system_prompt'] = system_prompt
            
            # Set tool restrictions if provided
            # If enable_all_tools is True and no allowed_tools specified, don't set any restrictions
            enable_all_tools = kwargs.get('enable_all_tools', self._enable_all_tools)
            enable_web_search = kwargs.get('enable_web_search', self._enable_web_search)
            allowed_tools = kwargs.get('allowed_tools', self._allowed_tools)
            disallowed_tools = kwargs.get('disallowed_tools', self._disallowed_tools)
            
            # Add WebSearch to allowed tools if web search is enabled
            if enable_web_search and allowed_tools is not None and 'WebSearch' not in allowed_tools:
                allowed_tools = allowed_tools + ['WebSearch']
            
            # Only set tool restrictions if we're not enabling all tools or if specific tools are provided
            if not enable_all_tools or allowed_tools:
                if allowed_tools:
                    options_dict['allowed_tools'] = allowed_tools
                
                if disallowed_tools:
                    options_dict['disallowed_tools'] = disallowed_tools
            
            # If enable_all_tools is True and no allowed_tools, Claude will have access to all native tools
            if enable_all_tools and not allowed_tools:
                if self.verbose:
                    logger.info("Enabling all native Claude tools (including WebSearch)")
            
            # Set permission mode - default to bypassPermissions for smoother operation
            permission_mode = kwargs.get('permission_mode', 'bypassPermissions')
            options_dict['permission_mode'] = permission_mode
            if self.verbose:
                logger.info(f"Permission mode: {permission_mode}")
            
            # Set current working directory to ensure files are created in the right place
            import os
            cwd = kwargs.get('cwd', os.getcwd())
            options_dict['cwd'] = cwd
            if self.verbose:
                logger.info(f"Working directory: {cwd}")
            
            # Create options
            options = ClaudeCodeOptions(**options_dict)
            
            # Log request details if verbose
            if self.verbose:
                logger.info("Claude SDK Request:")
                logger.info(f"  Prompt length: {len(prompt)} characters")
                logger.info(f"  System prompt: {system_prompt}")
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
                                    tool_input = getattr(content_block, 'input', {})
                                    
                                    # Enhanced tool display
                                    print(f"\n{'='*50}", flush=True)
                                    print(f"[TOOL USE: {tool_name}]", flush=True)
                                    print(f"  ID: {tool_id[:12]}...", flush=True)
                                    
                                    # Display input parameters
                                    if tool_input:
                                        print("  Input Parameters:", flush=True)
                                        for key, value in tool_input.items():
                                            # Truncate long values for display
                                            value_str = str(value)
                                            if len(value_str) > 100:
                                                value_str = value_str[:97] + "..."
                                            print(f"    - {key}: {value_str}", flush=True)
                                    
                                    print(f"{'='*50}", flush=True)
                                    
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
                        
                        # Extract and display tool results from UserMessage
                        if hasattr(message, 'content'):
                            content = message.content
                            # Handle both string and list content
                            if isinstance(content, list):
                                for content_item in content:
                                    if hasattr(content_item, '__class__'):
                                        item_type = content_item.__class__.__name__
                                        if item_type == 'ToolResultBlock':
                                            print("\n[TOOL RESULT]", flush=True)
                                            tool_use_id = getattr(content_item, 'tool_use_id', 'unknown')
                                            print(f"  For Tool ID: {tool_use_id[:12]}...", flush=True)
                                            
                                            result_content = getattr(content_item, 'content', None)
                                            is_error = getattr(content_item, 'is_error', False)
                                            
                                            if is_error:
                                                print("  Status: ERROR", flush=True)
                                            else:
                                                print("  Status: Success", flush=True)
                                            
                                            if result_content:
                                                print("  Output:", flush=True)
                                                # Handle different content types
                                                if isinstance(result_content, str):
                                                    # Truncate long outputs
                                                    if len(result_content) > 500:
                                                        print(f"    {result_content[:497]}...", flush=True)
                                                    else:
                                                        print(f"    {result_content}", flush=True)
                                                elif isinstance(result_content, list):
                                                    for item in result_content[:3]:  # Show first 3 items
                                                        print(f"    - {item}", flush=True)
                                                    if len(result_content) > 3:
                                                        print(f"    ... and {len(result_content) - 3} more items", flush=True)
                                            print(f"{'='*50}", flush=True)
                
                elif msg_type == 'ToolResultMessage':
                    # Tool result message
                    if self.verbose:
                        logger.debug("Tool result message received")
                        
                        # Extract and display content from ToolResultMessage
                        if hasattr(message, 'tool_use_id'):
                            print("\n[TOOL RESULT MESSAGE]", flush=True)
                            print(f"  Tool ID: {message.tool_use_id[:12]}...", flush=True)
                        
                        if hasattr(message, 'content'):
                            content = message.content
                            if content:
                                print("  Content:", flush=True)
                                if isinstance(content, str):
                                    if len(content) > 500:
                                        print(f"    {content[:497]}...", flush=True)
                                    else:
                                        print(f"    {content}", flush=True)
                                elif isinstance(content, list):
                                    for item in content[:3]:
                                        print(f"    - {item}", flush=True)
                                    if len(content) > 3:
                                        print(f"    ... and {len(content) - 3} more items", flush=True)
                        
                        if hasattr(message, 'is_error') and message.is_error:
                            print("  Error: True", flush=True)
                        
                        print(f"{'='*50}", flush=True)
                
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
                logger.info("Claude SDK Response:")
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
