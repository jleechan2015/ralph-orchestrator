#!/usr/bin/env python3
# ABOUTME: Simple test script to verify orchestrator basic functionality
# ABOUTME: Tests the complete flow with a simple task

import os
import sys
import time
import subprocess
from pathlib import Path

def test_orchestrator():
    """Test the orchestrator with a simple task."""
    print("Testing Ralph Orchestrator...")
    
    # Create a simple test prompt
    prompt_file = Path("test_prompt_simple.md")
    prompt_content = """# Simple Test Task

Please write a simple hello world message.

When you're done, add TASK_COMPLETE on its own line at the end of this file.
"""
    
    # Write the prompt file
    prompt_file.write_text(prompt_content)
    print(f"Created test prompt: {prompt_file}")
    
    try:
        # Run the orchestrator with claude (most likely to work)
        print("\nRunning orchestrator with Claude...")
        result = subprocess.run(
            ["uv", "run", "python", "-m", "ralph_orchestrator", 
             "--prompt", str(prompt_file),
             "--tool", "claude",
             "--max-iterations", "2"],
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )
        
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output (first 500 chars):\n{result.stdout[:500]}")
        if result.stderr:
            print(f"Errors (first 500 chars):\n{result.stderr[:500]}")
        
        # Check if task was completed
        final_content = prompt_file.read_text()
        if "TASK_COMPLETE" in final_content:
            print("\n✅ Task marked as complete!")
            print(f"Final prompt content:\n{final_content}")
            return True
        else:
            print("\n❌ Task not completed")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ Orchestrator timed out")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        # Clean up
        if prompt_file.exists():
            prompt_file.unlink()
            print(f"Cleaned up test prompt")

if __name__ == "__main__":
    success = test_orchestrator()
    sys.exit(0 if success else 1)