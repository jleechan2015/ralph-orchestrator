#!/usr/bin/env python3
"""Real integration test for ralph orchestrator with actual AI agents"""

import subprocess
import time
from pathlib import Path
import sys

def test_q_chat():
    """Test actual q chat integration"""
    print("Testing Q Chat integration...")
    
    # Create test prompt
    prompt_path = Path(".agent/TEST_Q_REAL.md")
    prompt_path.write_text("""# Task: Calculate Factorial

Write a Python function that calculates the factorial of 5 and prints the result.
When done, add TASK_COMPLETE to this file.

<!-- Add TASK_COMPLETE here when done -->
""")
    
    # Run ralph with q
    cmd = ["./ralph_orchestrator.py", "--agent", "q", "--prompt", str(prompt_path), "--max-iterations", "3", "--verbose"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Check if TASK_COMPLETE was added
    content = prompt_path.read_text()
    if "TASK_COMPLETE" in content:
        print("✓ Q Chat successfully added TASK_COMPLETE")
        return True
    else:
        print("✗ Q Chat did not add TASK_COMPLETE")
        print(f"Prompt content:\n{content}")
        print(f"Command output:\n{result.stdout[:500]}")
        return False

def test_claude():
    """Test actual Claude integration"""
    print("\nTesting Claude integration...")
    
    # Create test prompt
    prompt_path = Path(".agent/TEST_CLAUDE_REAL.md")
    prompt_path.write_text("""# Task: Fibonacci

Write a Python function that returns the 10th Fibonacci number.
When done, add TASK_COMPLETE to this file.

<!-- Add TASK_COMPLETE here when done -->
""")
    
    # Run ralph with Claude
    cmd = ["./ralph_orchestrator.py", "--agent", "claude", "--prompt", str(prompt_path), "--max-iterations", "3", "--verbose"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Check if TASK_COMPLETE was added
    content = prompt_path.read_text()
    if "TASK_COMPLETE" in content:
        print("✓ Claude successfully added TASK_COMPLETE")
        return True
    else:
        print("✗ Claude did not add TASK_COMPLETE")
        print(f"Prompt content:\n{content}")
        print(f"Command output:\n{result.stdout[:500]}")
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("RALPH ORCHESTRATOR - REAL INTEGRATION TESTS")
    print("=" * 60)
    
    results = []
    
    # Test Q Chat
    try:
        results.append(("Q Chat", test_q_chat()))
    except Exception as e:
        print(f"Q Chat test failed with error: {e}")
        results.append(("Q Chat", False))
    
    # Test Claude
    try:
        results.append(("Claude", test_claude()))
    except Exception as e:
        print(f"Claude test failed with error: {e}")
        results.append(("Claude", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    # Return exit code
    all_passed = all(r[1] for r in results)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()