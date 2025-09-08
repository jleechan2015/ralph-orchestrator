#!/usr/bin/env python3
# ABOUTME: Test script to debug Claude SDK streaming output
# ABOUTME: Directly tests the Claude adapter streaming functionality

import asyncio
import logging
from src.ralph_orchestrator.adapters.claude import ClaudeAdapter

logging.basicConfig(level=logging.DEBUG)

async def test_streaming():
    """Test Claude SDK streaming output."""
    print("Creating Claude adapter with verbose=True...")
    adapter = ClaudeAdapter(verbose=True)
    
    if not adapter.available:
        print("Claude SDK not available!")
        return
    
    print("Claude adapter available, sending test prompt...")
    
    # Simple test prompt
    prompt = "Say 'Hello World' and nothing else."
    
    response = await adapter.aexecute(prompt)
    
    print(f"\nFinal response success: {response.success}")
    print(f"Final output length: {len(response.output) if response.output else 0}")
    if response.error:
        print(f"Error: {response.error}")

if __name__ == "__main__":
    asyncio.run(test_streaming())