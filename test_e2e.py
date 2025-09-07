#!/usr/bin/env python3
# ABOUTME: End-to-end test demonstrating ralph orchestrator with a real task
# ABOUTME: Shows the system working with a coding task that requires multiple iterations

"""End-to-end test for Ralph Orchestrator with a real coding task."""

import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import time
import signal

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ralph_orchestrator.orchestrator import RalphOrchestrator


def create_test_environment():
    """Create a test environment with a coding task."""
    temp_dir = tempfile.mkdtemp(prefix="ralph_e2e_")
    print(f"Created test directory: {temp_dir}")
    
    # Create prompt file with a real task
    prompt_file = Path(temp_dir) / "PROMPT.md"
    prompt_content = """# Task: Create a Simple Calculator

Please create a Python calculator module with the following requirements:

1. Create a file called `calculator.py`
2. Implement these functions:
   - `add(a, b)` - returns a + b
   - `subtract(a, b)` - returns a - b
   - `multiply(a, b)` - returns a * b
   - `divide(a, b)` - returns a / b (handle division by zero)

3. Create a file called `test_calculator.py` with unit tests
4. Make sure all functions have docstrings

When you're done, add "TASK_COMPLETE" to this prompt file.

## Current Status
- [ ] calculator.py created
- [ ] Functions implemented
- [ ] test_calculator.py created
- [ ] Tests pass
"""
    prompt_file.write_text(prompt_content)
    
    # Initialize git repo
    original_dir = os.getcwd()
    os.chdir(temp_dir)
    
    subprocess.run(["git", "init"], capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], capture_output=True)
    subprocess.run(["git", "add", "-A"], capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], capture_output=True)
    
    os.chdir(original_dir)
    return temp_dir, prompt_file


def run_orchestrator_with_timeout(temp_dir, prompt_file, max_time=60):
    """Run the orchestrator with a timeout."""
    original_dir = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # Determine which tool to use
        primary_tool = None
        if subprocess.run(["which", "q"], capture_output=True).returncode == 0:
            primary_tool = "qchat"
            print("Using Q Chat as primary tool")
        elif subprocess.run(["claude", "--version"], capture_output=True).returncode == 0:
            primary_tool = "claude"
            print("Using Claude as primary tool")
        else:
            print("No supported tools available")
            return None
        
        # Create orchestrator
        orchestrator = RalphOrchestrator(
            prompt_file=str(prompt_file),
            primary_tool=primary_tool,
            max_iterations=10,  # Limit iterations for testing
            max_runtime=max_time,
            track_costs=True,
            checkpoint_interval=2
        )
        
        print(f"\nStarting orchestrator with {primary_tool}...")
        print("This will attempt to complete the calculator task.")
        print("Press Ctrl+C to stop.\n")
        
        start_time = time.time()
        
        # Set up timeout
        def timeout_handler(signum, frame):
            print("\nReached timeout, stopping orchestrator...")
            orchestrator.stop_requested = True
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(max_time)
        
        # Run orchestrator
        orchestrator.run()
        
        # Cancel alarm
        signal.alarm(0)
        
        elapsed = time.time() - start_time
        
        return {
            "success": True,
            "iterations": orchestrator.metrics.iterations,
            "successful_iterations": orchestrator.metrics.successful_iterations,
            "failed_iterations": orchestrator.metrics.failed_iterations,
            "errors": orchestrator.metrics.errors,
            "elapsed_time": elapsed,
            "total_cost": orchestrator.cost_tracker.total_cost if orchestrator.cost_tracker else 0
        }
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return {
            "success": False,
            "interrupted": True
        }
    except Exception as e:
        print(f"\nError: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        os.chdir(original_dir)


def check_results(temp_dir):
    """Check if the task was completed successfully."""
    results = {
        "calculator_exists": False,
        "test_exists": False,
        "functions_implemented": False,
        "task_marked_complete": False
    }
    
    # Check if calculator.py exists
    calc_file = Path(temp_dir) / "calculator.py"
    if calc_file.exists():
        results["calculator_exists"] = True
        content = calc_file.read_text()
        
        # Check for all required functions
        required_functions = ["def add", "def subtract", "def multiply", "def divide"]
        if all(func in content for func in required_functions):
            results["functions_implemented"] = True
    
    # Check if test file exists
    test_file = Path(temp_dir) / "test_calculator.py"
    if test_file.exists():
        results["test_exists"] = True
    
    # Check if task is marked complete
    prompt_file = Path(temp_dir) / "PROMPT.md"
    if prompt_file.exists():
        content = prompt_file.read_text()
        if "TASK_COMPLETE" in content:
            results["task_marked_complete"] = True
    
    return results


def main():
    """Run the end-to-end test."""
    print("="*60)
    print("RALPH ORCHESTRATOR - END-TO-END TEST")
    print("="*60)
    print("\nThis test will create a calculator module using AI.")
    print("It demonstrates the full orchestration loop.\n")
    
    # Create test environment
    temp_dir, prompt_file = create_test_environment()
    
    try:
        # Run orchestrator
        result = run_orchestrator_with_timeout(temp_dir, prompt_file, max_time=120)
        
        if result and result.get("success"):
            print("\n" + "="*60)
            print("ORCHESTRATION RESULTS")
            print("="*60)
            print(f"Completed in {result['elapsed_time']:.2f} seconds")
            print(f"Total iterations: {result['iterations']}")
            print(f"Successful iterations: {result['successful_iterations']}")
            print(f"Failed iterations: {result['failed_iterations']}")
            print(f"Errors: {result['errors']}")
            print(f"Total cost: ${result['total_cost']:.4f}")
            
            # Check task completion
            print("\n" + "="*60)
            print("TASK VERIFICATION")
            print("="*60)
            
            task_results = check_results(temp_dir)
            for check, passed in task_results.items():
                status = "✓" if passed else "✗"
                print(f"{status} {check.replace('_', ' ').title()}")
            
            # Show generated files
            print("\n" + "="*60)
            print("GENERATED FILES")
            print("="*60)
            
            for file in Path(temp_dir).glob("*.py"):
                print(f"\n{file.name}:")
                print("-" * 40)
                content = file.read_text()
                if len(content) > 500:
                    print(content[:500] + "...\n[truncated]")
                else:
                    print(content)
            
            # Overall success
            all_passed = all(task_results.values())
            print("\n" + "="*60)
            if all_passed:
                print("✓ END-TO-END TEST PASSED")
            else:
                print("✗ END-TO-END TEST FAILED - Task not fully completed")
            print("="*60)
            
            return 0 if all_passed else 1
        else:
            print("\n✗ Orchestration failed")
            if result:
                print(f"Reason: {result}")
            return 1
            
    finally:
        # Cleanup
        print(f"\nCleaning up {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())