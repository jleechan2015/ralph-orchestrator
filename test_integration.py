#!/usr/bin/env python3
# ABOUTME: Comprehensive integration tests for ralph-orchestrator
# ABOUTME: Tests both q chat and claude CLI integrations with various scenarios

"""Integration tests for Ralph Orchestrator with real CLI tools."""

import os
import sys
import subprocess
import tempfile
import time
import json
from pathlib import Path
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ralph_orchestrator.orchestrator import RalphOrchestrator
from src.ralph_orchestrator.adapters.claude import ClaudeAdapter
from src.ralph_orchestrator.adapters.qchat import QChatAdapter


class IntegrationTestRunner:
    """Run integration tests for Ralph Orchestrator."""
    
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="ralph_test_"))
        self.results = []
        print(f"Test directory: {self.test_dir}")
    
    def cleanup(self):
        """Clean up test directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def create_test_prompt(self, filename: str, content: str) -> Path:
        """Create a test prompt file."""
        prompt_path = self.test_dir / filename
        prompt_path.write_text(content)
        return prompt_path
    
    def run_test(self, name: str, tool: str, prompt_content: str, 
                 expected_contains: str = None, max_iterations: int = 1) -> bool:
        """Run a single integration test."""
        print(f"\n{'='*60}")
        print(f"Running test: {name}")
        print(f"Tool: {tool}")
        print(f"{'='*60}")
        
        try:
            # Create prompt file
            prompt_file = self.create_test_prompt(f"{name}_{tool}.md", prompt_content)
            
            # Run orchestrator
            start_time = time.time()
            orchestrator = RalphOrchestrator(
                prompt_file=str(prompt_file),
                primary_tool=tool,
                max_iterations=max_iterations,
                max_runtime=60,  # 1 minute timeout per test
                track_costs=False
            )
            
            orchestrator.run()
            elapsed = time.time() - start_time
            
            # Check results
            result_content = prompt_file.read_text()
            
            # Check if TASK_COMPLETE is present
            success = "TASK_COMPLETE" in result_content
            
            # Check expected content if provided
            if expected_contains and success:
                success = expected_contains in result_content
            
            # Print results
            print(f"✓ Test passed" if success else "✗ Test failed")
            print(f"Time: {elapsed:.2f}s")
            print(f"Result:\n{result_content}\n")
            
            self.results.append({
                "test": name,
                "tool": tool,
                "success": success,
                "time": elapsed,
                "output": result_content
            })
            
            return success
            
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            self.results.append({
                "test": name,
                "tool": tool,
                "success": False,
                "error": str(e)
            })
            return False
    
    def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*60)
        print("RALPH ORCHESTRATOR INTEGRATION TESTS")
        print("="*60)
        
        # Test 1: Simple math with q chat
        self.run_test(
            name="simple_math",
            tool="qchat",
            prompt_content="Calculate 15 + 27 and write the answer below.\n\nAnswer: ",
            expected_contains="42"
        )
        
        # Test 2: Simple math with claude
        self.run_test(
            name="simple_math",
            tool="claude",
            prompt_content="Calculate 8 * 9 and write the answer below.\n\nAnswer: ",
            expected_contains="72"
        )
        
        # Test 3: Code generation with q chat
        self.run_test(
            name="code_generation",
            tool="qchat",
            prompt_content="""Write a Python function that reverses a string.

```python
def reverse_string(s):
    # Add implementation here
    pass
```

Complete the function implementation above.""",
            expected_contains="return"
        )
        
        # Test 4: Code generation with claude
        self.run_test(
            name="code_generation",
            tool="claude",
            prompt_content="""Write a Python function that checks if a number is prime.

```python
def is_prime(n):
    # Add implementation here
    pass
```

Complete the function implementation above.""",
            expected_contains="return"
        )
        
        # Test 5: Multi-step task with q chat
        self.run_test(
            name="multi_step",
            tool="qchat",
            prompt_content="""Complete the following tasks:
1. Calculate 5 * 6
2. Add 10 to the result
3. Write the final answer below

Final answer: """,
            expected_contains="40"
        )
        
        # Test 6: Multi-step task with claude
        self.run_test(
            name="multi_step",
            tool="claude",
            prompt_content="""Complete the following tasks:
1. Calculate 100 / 4
2. Multiply the result by 2
3. Write the final answer below

Final answer: """,
            expected_contains="50"
        )
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("success", False))
        failed = total - passed
        
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(passed/total)*100:.1f}%" if total > 0 else "N/A")
        
        print("\nDetailed Results:")
        for result in self.results:
            status = "✓" if result.get("success", False) else "✗"
            name = f"{result['test']} ({result['tool']})"
            if result.get("error"):
                print(f"{status} {name}: ERROR - {result['error']}")
            else:
                time_str = f"{result.get('time', 0):.2f}s"
                print(f"{status} {name}: {time_str}")
    
    def save_results(self):
        """Save test results to file."""
        results_file = Path(".ralph") / f"test_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")


def check_prerequisites():
    """Check if required CLI tools are available."""
    print("Checking prerequisites...")
    
    tools_available = {}
    
    # Check q chat
    try:
        result = subprocess.run(["which", "q"], capture_output=True, text=True)
        tools_available["q"] = result.returncode == 0
    except:
        tools_available["q"] = False
    
    # Check claude
    try:
        result = subprocess.run(["which", "claude"], capture_output=True, text=True)
        tools_available["claude"] = result.returncode == 0
    except:
        tools_available["claude"] = False
    
    print(f"✓ q chat: {'Available' if tools_available['q'] else 'Not found'}")
    print(f"✓ claude: {'Available' if tools_available['claude'] else 'Not found'}")
    
    if not any(tools_available.values()):
        print("\n❌ No CLI tools available. Please install at least one:")
        print("  - q: https://github.com/qwen/q-cli")
        print("  - claude: npm install -g @anthropic-ai/claude-code")
        return False
    
    return True


def main():
    """Main test runner."""
    print("Ralph Orchestrator Integration Test Suite")
    print("=========================================\n")
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Run tests
    runner = IntegrationTestRunner()
    try:
        runner.run_all_tests()
    finally:
        runner.cleanup()
    
    # Return exit code based on results
    all_passed = all(r.get("success", False) for r in runner.results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()