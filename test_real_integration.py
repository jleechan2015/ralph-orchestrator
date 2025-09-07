#!/usr/bin/env python3
# ABOUTME: Real integration test script for testing with actual CLI tools
# ABOUTME: Tests q chat and claude commands if they're available on the system

"""Real integration tests with actual CLI tools."""

import sys
import os
import subprocess
import tempfile
import json
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ralph_orchestrator.adapters.claude import ClaudeAdapter
from ralph_orchestrator.adapters.qchat import QChatAdapter
from ralph_orchestrator.adapters.gemini import GeminiAdapter
from ralph_orchestrator.orchestrator import RalphOrchestrator


def check_tool_availability(tool_name):
    """Check if a tool is available."""
    try:
        if tool_name == "claude":
            result = subprocess.run(["claude", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        elif tool_name == "q":
            result = subprocess.run(["which", "q"], capture_output=True, timeout=5)
            return result.returncode == 0
        elif tool_name == "gemini":
            result = subprocess.run(["gemini", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
    except:
        return False
    return False


def test_qchat_real():
    """Test Q Chat with real command."""
    print("\n" + "="*50)
    print("Testing Q Chat Integration")
    print("="*50)
    
    if not check_tool_availability("q"):
        print("❌ Q Chat is not available - skipping test")
        return False
    
    adapter = QChatAdapter()
    print(f"✓ Q Chat adapter initialized: available={adapter.available}")
    
    # Test simple prompt
    test_prompt = "Say 'Hello from Q Chat test' and nothing else"
    print(f"Testing with prompt: {test_prompt}")
    
    response = adapter.execute(test_prompt, timeout=30)
    
    if response.success:
        print(f"✓ Q Chat responded successfully")
        print(f"  Output: {response.output[:100]}...")
        if response.tokens_used:
            print(f"  Tokens: {response.tokens_used}")
        print(f"  Cost: ${adapter.estimate_cost(test_prompt):.4f}")
        return True
    else:
        print(f"❌ Q Chat failed: {response.error}")
        return False


def test_claude_real():
    """Test Claude with real command."""
    print("\n" + "="*50)
    print("Testing Claude Integration")
    print("="*50)
    
    if not check_tool_availability("claude"):
        print("❌ Claude is not available - skipping test")
        return False
    
    adapter = ClaudeAdapter()
    print(f"✓ Claude adapter initialized: available={adapter.available}")
    
    # Test simple prompt
    test_prompt = "Say 'Hello from Claude test' and nothing else"
    print(f"Testing with prompt: {test_prompt}")
    
    response = adapter.execute(test_prompt, timeout=30)
    
    if response.success:
        print(f"✓ Claude responded successfully")
        print(f"  Output: {response.output[:100]}...")
        if response.tokens_used:
            print(f"  Tokens: {response.tokens_used}")
        if response.cost:
            print(f"  Cost: ${response.cost:.4f}")
        return True
    else:
        print(f"❌ Claude failed: {response.error}")
        return False


def test_gemini_real():
    """Test Gemini with real command."""
    print("\n" + "="*50)
    print("Testing Gemini Integration")
    print("="*50)
    
    if not check_tool_availability("gemini"):
        print("❌ Gemini is not available - skipping test")
        return False
    
    adapter = GeminiAdapter()
    print(f"✓ Gemini adapter initialized: available={adapter.available}")
    
    # Test simple prompt
    test_prompt = "Say 'Hello from Gemini test' and nothing else"
    print(f"Testing with prompt: {test_prompt}")
    
    response = adapter.execute(test_prompt, timeout=30)
    
    if response.success:
        print(f"✓ Gemini responded successfully")
        print(f"  Output: {response.output[:100]}...")
        if response.tokens_used:
            print(f"  Tokens: {response.tokens_used}")
        if response.cost:
            print(f"  Cost: ${response.cost:.4f}")
        return True
    else:
        print(f"❌ Gemini failed: {response.error}")
        return False


def test_orchestrator_real():
    """Test orchestrator with real tools."""
    print("\n" + "="*50)
    print("Testing Full Orchestrator")
    print("="*50)
    
    # Find available tool
    primary_tool = None
    if check_tool_availability("q"):
        primary_tool = "qchat"
        print("Using Q Chat as primary tool")
    elif check_tool_availability("claude"):
        primary_tool = "claude"
        print("Using Claude as primary tool")
    elif check_tool_availability("gemini"):
        primary_tool = "gemini"
        print("Using Gemini as primary tool")
    else:
        print("❌ No tools available - skipping orchestrator test")
        return False
    
    # Create temp directory for test
    temp_dir = tempfile.mkdtemp()
    prompt_file = Path(temp_dir) / "PROMPT.md"
    
    # Create a simple test prompt
    prompt_content = """Please respond with exactly this text:
"Test successful. TASK_COMPLETE"

This is a test of the Ralph Orchestrator system.
"""
    prompt_file.write_text(prompt_content)
    
    # Change to temp directory
    original_dir = os.getcwd()
    os.chdir(temp_dir)
    
    # Initialize git repo
    subprocess.run(["git", "init"], capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], capture_output=True)
    
    print(f"Created test environment in {temp_dir}")
    
    try:
        # Create orchestrator
        orchestrator = RalphOrchestrator(
            prompt_file=str(prompt_file),
            primary_tool=primary_tool,
            max_iterations=3,
            max_runtime=60,
            track_costs=True,
            checkpoint_interval=2
        )
        
        print("Starting orchestrator...")
        start_time = time.time()
        
        # Run for a short time
        orchestrator.run()
        
        elapsed = time.time() - start_time
        
        print(f"\n✓ Orchestrator completed in {elapsed:.2f} seconds")
        print(f"  Iterations: {orchestrator.metrics.iterations}")
        print(f"  Successful: {orchestrator.metrics.successful_iterations}")
        print(f"  Failed: {orchestrator.metrics.failed_iterations}")
        
        if orchestrator.cost_tracker:
            print(f"  Total cost: ${orchestrator.cost_tracker.total_cost:.4f}")
        
        return orchestrator.metrics.successful_iterations > 0
        
    finally:
        # Cleanup
        os.chdir(original_dir)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"Cleaned up temp directory")


def main():
    """Run all real integration tests."""
    print("\n" + "="*60)
    print("RALPH ORCHESTRATOR - REAL INTEGRATION TESTS")
    print("="*60)
    print("\nThis will test the actual CLI tools if they are available.")
    print("Make sure you have configured API keys if needed.\n")
    
    results = {
        "Q Chat": test_qchat_real(),
        "Claude": test_claude_real(),
        "Gemini": test_gemini_real(),
        "Orchestrator": test_orchestrator_real()
    }
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for tool, passed in results.items():
        if passed is None:
            continue
        status = "✓ PASSED" if passed else "✗ FAILED/SKIPPED"
        print(f"{tool:20} {status}")
    
    # Return exit code
    all_passed = all(r for r in results.values() if r is not None)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()