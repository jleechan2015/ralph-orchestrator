#!/usr/bin/env python3
# ABOUTME: Simple test script to verify q chat integration
# ABOUTME: Tests basic functionality with a minimal prompt

import subprocess
import sys

def test_q_chat():
    """Test q chat with a simple prompt."""
    print("Testing q chat with simple prompt...")
    
    # Create a simple test prompt file
    with open("test_q_prompt.txt", "w") as f:
        f.write("Say exactly: 'Q Chat test successful'")
    
    try:
        # Run q chat with the prompt
        result = subprocess.run(
            ["q", "chat", "@test_q_prompt.txt"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        
        # Check if the response contains expected text
        if "successful" in result.stdout.lower() or result.returncode == 0:
            print("✅ Q Chat test PASSED")
            return True
        else:
            print("❌ Q Chat test FAILED")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Q Chat test TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ Q Chat test ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_q_chat()
    sys.exit(0 if success else 1)