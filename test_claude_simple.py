#!/usr/bin/env python3
# ABOUTME: Simple test script to verify claude integration
# ABOUTME: Tests basic functionality with a minimal prompt

import subprocess
import sys

def test_claude():
    """Test claude with a simple prompt."""
    print("Testing claude with simple prompt...")
    
    try:
        # Run claude with a simple prompt
        result = subprocess.run(
            ["claude", "-p", "Say exactly: 'Claude test successful'"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout[:500]}")  # First 500 chars
        if result.stderr:
            print(f"Error: {result.stderr[:500]}")
        
        # Check if the response contains expected text
        if "successful" in result.stdout.lower() and result.returncode == 0:
            print("✅ Claude test PASSED")
            return True
        else:
            print("❌ Claude test FAILED")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Claude test TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ Claude test ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_claude()
    sys.exit(0 if success else 1)