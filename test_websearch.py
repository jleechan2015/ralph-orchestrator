#!/usr/bin/env python3
# ABOUTME: Test script to verify WebSearch functionality with Claude adapter
# ABOUTME: Demonstrates that Claude can use WebSearch through Ralph Orchestrator

"""Test WebSearch functionality with Claude adapter."""

import asyncio
from src.ralph_orchestrator.adapters.claude import ClaudeAdapter


def test_websearch_enabled():
    """Test that WebSearch is enabled by default in Claude adapter."""
    
    print("\n=== Testing WebSearch with Claude Adapter ===\n")
    
    # Create adapter
    adapter = ClaudeAdapter(verbose=True)
    
    # Configure with WebSearch enabled (should be default)
    adapter.configure(enable_web_search=True)
    
    if not adapter.available:
        print("Claude SDK not available. Please install claude-code-sdk")
        return False
    
    # Test prompt that requires web search
    test_prompt = """
    Please search the web for the latest news about Python 3.13 release.
    Use the WebSearch tool to find current information.
    Provide a brief summary of what you find.
    """
    
    print("Testing WebSearch capability...")
    print(f"Prompt: {test_prompt[:100]}...")
    
    # Execute with WebSearch enabled
    response = adapter.execute(
        test_prompt,
        enable_all_tools=True,
        enable_web_search=True
    )
    
    if response.success:
        print("\n✓ WebSearch test successful!")
        print(f"Response preview: {response.output[:500]}...")
        return True
    else:
        print(f"\n✗ WebSearch test failed: {response.error}")
        return False


def test_websearch_with_specific_tools():
    """Test WebSearch with specific allowed tools list."""
    
    print("\n=== Testing WebSearch with Specific Tools List ===\n")
    
    adapter = ClaudeAdapter(verbose=False)
    
    # Configure with specific tools including WebSearch
    adapter.configure(
        allowed_tools=['WebSearch', 'Read', 'Write'],
        enable_web_search=True
    )
    
    if not adapter.available:
        print("Claude SDK not available")
        return False
    
    test_prompt = "Search for information about the latest AI developments and create a summary."
    
    print("Testing with allowed_tools=['WebSearch', 'Read', 'Write']...")
    
    response = adapter.execute(
        test_prompt,
        allowed_tools=['WebSearch', 'Read', 'Write'],
        enable_web_search=True
    )
    
    if response.success:
        print("✓ Test with specific tools successful!")
        return True
    else:
        print(f"✗ Test failed: {response.error}")
        return False


async def test_async_websearch():
    """Test async WebSearch functionality."""
    
    print("\n=== Testing Async WebSearch ===\n")
    
    adapter = ClaudeAdapter(verbose=False)
    adapter.configure(enable_all_tools=True, enable_web_search=True)
    
    if not adapter.available:
        print("Claude SDK not available")
        return False
    
    test_prompts = [
        "What is the current weather in San Francisco?",
        "Find the latest stock price for Apple (AAPL)",
        "Search for recent developments in quantum computing"
    ]
    
    print("Running multiple WebSearch queries concurrently...")
    
    tasks = [
        adapter.aexecute(prompt, enable_all_tools=True, enable_web_search=True)
        for prompt in test_prompts
    ]
    
    responses = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in responses if r.success)
    print(f"\n✓ {success_count}/{len(test_prompts)} async searches completed successfully")
    
    return success_count == len(test_prompts)


def main():
    """Run all WebSearch tests."""
    
    print("\n" + "="*60)
    print(" WebSearch Functionality Tests for Ralph Claude Adapter")
    print("="*60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Basic WebSearch
    if test_websearch_enabled():
        tests_passed += 1
    
    # Test 2: WebSearch with specific tools
    if test_websearch_with_specific_tools():
        tests_passed += 1
    
    # Test 3: Async WebSearch
    if asyncio.run(test_async_websearch()):
        tests_passed += 1
    
    print("\n" + "="*60)
    print(f" Test Results: {tests_passed}/{total_tests} passed")
    print("="*60)
    
    if tests_passed == total_tests:
        print("\n✓ All WebSearch tests passed!")
        print("\nWebSearch is now available in Ralph's Claude adapter.")
        print("You can use it by:")
        print("1. Running: ralph -a claude")
        print("2. Or in code: adapter.configure(enable_web_search=True)")
    else:
        print(f"\n⚠ {total_tests - tests_passed} test(s) failed")
        print("Please check the error messages above.")


if __name__ == "__main__":
    main()