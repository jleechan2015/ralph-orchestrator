#!/usr/bin/env python3
# ABOUTME: Manual test script for Q Chat adapter
# ABOUTME: Tests basic functionality without mocking complexity

"""Manual test for Q Chat adapter functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ralph_orchestrator.adapters.qchat import QChatAdapter

def test_adapter_basic():
    """Test basic adapter functionality."""
    print("Testing Q Chat Adapter...")
    
    # Create adapter
    adapter = QChatAdapter()
    print(f"✓ Adapter created: {adapter}")
    print(f"  - Name: {adapter.name}")
    print(f"  - Command: {adapter.command}")
    print(f"  - Available: {adapter.available}")
    
    # Test availability check
    is_available = adapter.check_availability()
    print(f"✓ Availability check: {is_available}")
    
    # Test cost estimation
    cost = adapter.estimate_cost("Test prompt")
    print(f"✓ Cost estimation: ${cost}")
    assert cost == 0.0, "Q chat should have zero cost"
    
    # Test prompt enhancement
    original = "Simple task"
    enhanced = adapter._enhance_prompt_with_instructions(original)
    print(f"✓ Prompt enhancement works")
    assert "ORCHESTRATION CONTEXT" in enhanced
    assert original in enhanced
    
    # Test idempotency of enhancement
    double_enhanced = adapter._enhance_prompt_with_instructions(enhanced)
    assert double_enhanced == enhanced
    print(f"✓ Prompt enhancement is idempotent")
    
    # Test resource management helpers
    adapter._make_non_blocking(None)  # Should not crash
    result = adapter._read_available(None)  # Should return empty string
    assert result == ""
    print(f"✓ Resource management helpers work")
    
    print("\n✅ All basic tests passed!")
    return True

def test_adapter_cleanup():
    """Test adapter cleanup."""
    print("\nTesting cleanup...")
    
    adapter = QChatAdapter()
    # Manually trigger cleanup
    adapter.__del__()
    print("✓ Cleanup executed without errors")
    
    return True

if __name__ == "__main__":
    try:
        success = test_adapter_basic()
        success = test_adapter_cleanup() and success
        
        if success:
            print("\n🎉 All manual tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)