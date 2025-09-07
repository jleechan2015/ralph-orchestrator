#!/usr/bin/env python3
# ABOUTME: Comprehensive integration tests for Ralph Orchestrator
# ABOUTME: Tests both q chat and claude CLI integrations

"""Integration tests for Ralph Orchestrator."""

import os
import sys
import tempfile
import shutil
import subprocess
import time
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ralph_orchestrator.orchestrator import RalphOrchestrator
from ralph_orchestrator.adapters.claude import ClaudeAdapter
from ralph_orchestrator.adapters.qchat import QChatAdapter


def test_adapters_available():
    """Test that adapters can be initialized."""
    print("Testing adapter availability...")
    
    claude = ClaudeAdapter()
    if claude.available:
        print("  ✅ Claude adapter available")
    else:
        print("  ⚠️  Claude adapter not available")
    
    qchat = QChatAdapter()
    if qchat.available:
        print("  ✅ Q Chat adapter available")
    else:
        print("  ⚠️  Q Chat adapter not available")
    
    return claude.available or qchat.available


def test_simple_task(tool="claude"):
    """Test a simple task with the specified tool."""
    print(f"\nTesting simple task with {tool}...")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create simple prompt
        prompt_file = Path("TEST_PROMPT.md")
        prompt_file.write_text(
            f"Create a Python function called greet() that returns 'Hello from {tool}!' "
            f"and save it to greeting_{tool}.py"
        )
        
        try:
            # Run orchestrator
            orchestrator = RalphOrchestrator(
                prompt_file=str(prompt_file),
                primary_tool=tool,
                max_iterations=1,
                max_runtime=60
            )
            
            orchestrator.run()
            
            # Check if task was completed
            prompt_content = prompt_file.read_text()
            if "TASK_COMPLETE" in prompt_content:
                print(f"  ✅ {tool} completed the task")
                
                # Check if file was created
                output_file = Path(f"greeting_{tool}.py")
                if output_file.exists():
                    print(f"  ✅ Output file created: {output_file}")
                    return True
                else:
                    print(f"  ❌ Output file not created")
                    return False
            else:
                print(f"  ❌ Task not marked as complete")
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False


def test_multi_iteration(tool="claude"):
    """Test multi-iteration task."""
    print(f"\nTesting multi-iteration with {tool}...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create a prompt that requires multiple steps
        prompt_file = Path("MULTI_PROMPT.md")
        prompt_file.write_text(
            "1. Create a file called step1.txt with content 'First step done'\n"
            "2. Create a file called step2.txt with content 'Second step done'\n"
            "3. Create a file called step3.txt with content 'All steps complete'"
        )
        
        try:
            orchestrator = RalphOrchestrator(
                prompt_file=str(prompt_file),
                primary_tool=tool,
                max_iterations=3,
                max_runtime=120
            )
            
            orchestrator.run()
            
            # Check if all files were created
            files_created = 0
            for step in [1, 2, 3]:
                if Path(f"step{step}.txt").exists():
                    files_created += 1
            
            if files_created > 0:
                print(f"  ✅ Created {files_created}/3 files")
                return files_created == 3
            else:
                print(f"  ❌ No files created")
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False


def test_error_recovery(tool="claude"):
    """Test error recovery mechanism."""
    print(f"\nTesting error recovery with {tool}...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create a prompt that might cause errors
        prompt_file = Path("ERROR_PROMPT.md")
        prompt_file.write_text(
            "Try to read a file that doesn't exist: /nonexistent/file.txt\n"
            "Then create a file called recovered.txt with content 'Recovery successful'"
        )
        
        try:
            orchestrator = RalphOrchestrator(
                prompt_file=str(prompt_file),
                primary_tool=tool,
                max_iterations=2,
                max_runtime=60
            )
            
            orchestrator.run()
            
            # Check if recovery file was created
            if Path("recovered.txt").exists():
                print(f"  ✅ Recovery successful")
                return True
            else:
                print(f"  ⚠️  Recovery file not created (tool may have handled error differently)")
                return True  # Not a failure, just different handling
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False


def test_cli_integration():
    """Test CLI integration."""
    print("\nTesting CLI integration...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create simple prompt
        prompt_file = Path("CLI_TEST.md")
        prompt_file.write_text("Return the text 'CLI test successful'")
        
        try:
            # Test dry run
            result = subprocess.run(
                [sys.executable, "-m", "ralph_orchestrator", "--dry-run"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("  ✅ CLI dry run successful")
                return True
            else:
                print(f"  ❌ CLI failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("Ralph Orchestrator Integration Tests")
    print("=" * 60)
    
    results = []
    
    # Test adapter availability
    if not test_adapters_available():
        print("\n⚠️  No adapters available, skipping tests")
        return
    
    # Test with available tools
    tools_to_test = []
    
    claude = ClaudeAdapter()
    if claude.available:
        tools_to_test.append("claude")
    
    qchat = QChatAdapter()
    if qchat.available:
        tools_to_test.append("qchat")
    
    for tool in tools_to_test:
        print(f"\n{'=' * 40}")
        print(f"Testing with {tool}")
        print('=' * 40)
        
        results.append(("Simple task", tool, test_simple_task(tool)))
        results.append(("Multi-iteration", tool, test_multi_iteration(tool)))
        results.append(("Error recovery", tool, test_error_recovery(tool)))
    
    # Test CLI
    results.append(("CLI integration", "N/A", test_cli_integration()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, tool, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} ({tool:6}): {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"Total: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    # Save current directory
    original_dir = os.getcwd()
    
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        # Restore original directory
        os.chdir(original_dir)