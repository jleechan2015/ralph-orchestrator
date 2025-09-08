#!/usr/bin/env python3
# ABOUTME: Test script for Claude adapter with all native tools enabled
# ABOUTME: Demonstrates using the SDK with full tool access

"""Test Claude SDK with all native tools enabled."""

import asyncio
import logging
from pathlib import Path
from src.ralph_orchestrator.adapters.claude import ClaudeAdapter

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_claude_with_all_tools():
    """Test Claude adapter with all native tools enabled."""
    
    print("\n" + "="*60)
    print("Testing Claude Adapter with All Native Tools Enabled")
    print("="*60 + "\n")
    
    # Create the adapter with verbose mode
    adapter = ClaudeAdapter(verbose=True)
    
    # Configure it to enable all tools
    adapter.configure(enable_all_tools=True)
    
    # Check availability
    if not adapter.available:
        print("❌ Claude SDK is not available. Please install claude-code-sdk")
        return
    
    print("✓ Claude SDK is available")
    print("✓ All native tools enabled")
    print()
    
    # Create a test prompt that would benefit from using various tools
    test_prompt = """
Please demonstrate your tool capabilities by:

1. List the files in the current directory
2. Read the README.md file if it exists
3. Search for any Python files that contain the word "adapter"
4. Create a simple test file called 'test_output.txt' with the content "Claude tools test successful!"
5. Show the current date and time

After completing these tasks, respond with a summary of what you did.
"""
    
    print("Sending test prompt to Claude...")
    print("-" * 40)
    print(test_prompt)
    print("-" * 40)
    print()
    
    try:
        # Execute the prompt with all tools enabled
        response = await adapter.aexecute(
            test_prompt,
            enable_all_tools=True,  # Explicitly enable all tools
            system_prompt="You are a helpful AI assistant with access to all available tools. Use them to complete the requested tasks."
        )
        
        if response.success:
            print("\n✓ Claude executed successfully!")
            print("\nResponse:")
            print("-" * 40)
            print(response.output)
            print("-" * 40)
            
            if response.tokens_used:
                print(f"\nTokens used: {response.tokens_used}")
            if response.cost:
                print(f"Estimated cost: ${response.cost:.4f}")
        else:
            print(f"\n❌ Execution failed: {response.error}")
            
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        logger.error("Execution error", exc_info=True)


async def test_claude_with_restricted_tools():
    """Test Claude adapter with restricted tool access."""
    
    print("\n" + "="*60)
    print("Testing Claude Adapter with Restricted Tools")
    print("="*60 + "\n")
    
    # Create the adapter
    adapter = ClaudeAdapter(verbose=True)
    
    # Configure with only specific tools allowed
    adapter.configure(
        allowed_tools=["Read", "Bash"],  # Only allow reading files and running bash commands
        enable_all_tools=False
    )
    
    if not adapter.available:
        print("❌ Claude SDK is not available")
        return
    
    print("✓ Claude SDK is available")
    print("✓ Tools restricted to: Read, Bash")
    print()
    
    test_prompt = """
Using only the Read and Bash tools available to you:
1. Use bash to list files in the current directory
2. Read the README.md file if it exists

Note: You should not be able to write files or use other tools.
"""
    
    print("Sending restricted test prompt to Claude...")
    print("-" * 40)
    
    try:
        response = await adapter.aexecute(
            test_prompt,
            allowed_tools=["Read", "Bash"],
            system_prompt="You are a helpful AI assistant with restricted tool access."
        )
        
        if response.success:
            print("\n✓ Claude executed with restricted tools!")
            print("\nResponse:")
            print("-" * 40)
            print(response.output)
            print("-" * 40)
        else:
            print(f"\n❌ Execution failed: {response.error}")
            
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")


async def main():
    """Run all tests."""
    
    print("\n" + "="*70)
    print(" Claude SDK Native Tools Test Suite")
    print("="*70)
    
    # Test 1: All tools enabled
    await test_claude_with_all_tools()
    
    # Wait a bit between tests
    await asyncio.sleep(2)
    
    # Test 2: Restricted tools
    await test_claude_with_restricted_tools()
    
    print("\n" + "="*70)
    print(" Tests Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())