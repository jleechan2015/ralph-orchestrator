#!/usr/bin/env python3
# ABOUTME: Comprehensive test of orchestrator with both q chat and claude
# ABOUTME: Verifies that the orchestrator can switch between tools and handle tasks

import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ralph_orchestrator.orchestrator import RalphOrchestrator
from ralph_orchestrator.adapters.claude import ClaudeAdapter
from ralph_orchestrator.adapters.qchat import QChatAdapter

def test_with_tool(tool_name, adapter_class):
    """Test orchestrator with a specific tool."""
    print(f"\n{'='*60}")
    print(f"Testing Orchestrator with {tool_name}")
    print('='*60)
    
    # Create temp directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write a simple test prompt
        prompt_file = Path(tmpdir) / "test_prompt.md"
        prompt_file.write_text(f"Write a Python function that returns the string 'Hello from {tool_name}'")
        
        # Create adapter
        adapter = adapter_class()
        if not adapter.available:
            print(f"❌ {tool_name} is not available")
            return False
            
        # Create orchestrator
        orchestrator = RalphOrchestrator(
            prompt_file=str(prompt_file),
            primary_tool=tool_name.lower().replace(" ", ""),
            max_iterations=3,
            track_costs=True
        )
        
        # Run orchestration
        try:
            orchestrator.run()
            
            # Check results
            metrics = orchestrator.metrics
            print(f"✅ Completed")
            print(f"   Iterations: {metrics.iterations}")
            print(f"   Success rate: {metrics.successful_iterations}/{metrics.iterations}")
            print(f"   Estimated cost: ${orchestrator.cost_tracker.total_cost if orchestrator.cost_tracker else 0:.4f}")
            
            return metrics.successful_iterations > 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

def main():
    """Run comprehensive orchestrator tests."""
    print("RALPH ORCHESTRATOR - COMPREHENSIVE INTEGRATION TEST")
    print("="*60)
    
    results = {}
    
    # Test with Q Chat
    results['qchat'] = test_with_tool("Q Chat", QChatAdapter)
    
    # Test with Claude
    results['claude'] = test_with_tool("Claude", ClaudeAdapter)
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    all_passed = True
    for tool, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{tool.upper():15} {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! The orchestrator is working with all tools.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())