# ABOUTME: Integration tests for Ralph Orchestrator with real CLI tools
# ABOUTME: Tests actual q chat and claude command execution with mocked outputs

"""Integration tests for Ralph Orchestrator with real tools."""

import unittest
import subprocess
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import time

from ralph_orchestrator.adapters.claude import ClaudeAdapter
from ralph_orchestrator.adapters.qchat import QChatAdapter
from ralph_orchestrator.adapters.gemini import GeminiAdapter
from ralph_orchestrator.orchestrator import RalphOrchestrator


class TestQChatIntegration(unittest.TestCase):
    """Integration tests for Q Chat adapter."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_prompt = "Write a simple hello world function in Python"
        self.adapter = QChatAdapter()
    
    @patch('subprocess.run')
    def test_qchat_basic_execution(self, mock_run):
        """Test basic q chat execution with mocked response."""
        # Mock availability check
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),  # which q
            MagicMock(
                returncode=0,
                stdout='def hello_world():\n    print("Hello, World!")\n',
                stderr=""
            )  # q chat command
        ]
        
        response = self.adapter.execute(self.test_prompt)
        
        self.assertTrue(response.success)
        self.assertIn("hello_world", response.output)
        self.assertIn("Hello, World!", response.output)
        
        # Verify the command was called correctly
        actual_call = mock_run.call_args_list[1]
        self.assertEqual(actual_call[0][0][0:2], ["q", "chat"])
        self.assertEqual(actual_call[0][0][2], self.test_prompt)
    
    @patch('subprocess.run')
    def test_qchat_with_complex_prompt(self, mock_run):
        """Test q chat with complex multi-line prompt."""
        complex_prompt = """Please help me with the following tasks:
1. Create a function to calculate fibonacci numbers
2. Make it efficient using memoization
3. Add proper documentation"""
        
        mock_run.side_effect = [
            MagicMock(returncode=0),  # which q
            MagicMock(
                returncode=0,
                stdout="""def fibonacci(n, memo={}):
    '''Calculate fibonacci number with memoization.
    
    Args:
        n: The position in the fibonacci sequence
        memo: Dictionary for memoization
    
    Returns:
        The fibonacci number at position n
    '''
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]""",
                stderr=""
            )
        ]
        
        response = self.adapter.execute(complex_prompt)
        
        self.assertTrue(response.success)
        self.assertIn("fibonacci", response.output)
        self.assertIn("memoization", response.output.lower())
    
    @patch('subprocess.run')
    def test_qchat_timeout_handling(self, mock_run):
        """Test q chat timeout handling."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # which q
            subprocess.TimeoutExpired(cmd=["q", "chat"], timeout=300)
        ]
        
        response = self.adapter.execute(self.test_prompt, timeout=1)
        
        self.assertFalse(response.success)
        self.assertIn("timed out", response.error)
    
    @patch('subprocess.run')
    def test_qchat_error_handling(self, mock_run):
        """Test q chat error handling."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # which q
            MagicMock(
                returncode=1,
                stdout="",
                stderr="Error: Invalid API key or configuration"
            )
        ]
        
        response = self.adapter.execute(self.test_prompt)
        
        self.assertFalse(response.success)
        self.assertIn("Invalid API key", response.error)
    
    def test_qchat_cost_is_free(self):
        """Test that q chat reports zero cost."""
        cost = self.adapter.estimate_cost("Any prompt of any length")
        self.assertEqual(cost, 0.0)


class TestClaudeIntegration(unittest.TestCase):
    """Integration tests for Claude adapter."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_prompt = "Explain recursion in one sentence"
        self.adapter = ClaudeAdapter()
    
    @patch('subprocess.run')
    def test_claude_basic_execution(self, mock_run):
        """Test basic claude execution with mocked response."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # --version check
            MagicMock(
                returncode=0,
                stdout="Recursion is a programming technique where a function calls itself to solve a problem by breaking it into smaller instances.",
                stderr="Tokens used: 25"
            )
        ]
        
        response = self.adapter.execute(self.test_prompt)
        
        self.assertTrue(response.success)
        self.assertIn("recursion", response.output.lower())
        self.assertEqual(response.tokens_used, 25)
        self.assertIsNotNone(response.cost)
        
        # Verify command structure
        actual_call = mock_run.call_args_list[1]
        self.assertEqual(actual_call[0][0][0:3], ["claude", "-p", self.test_prompt])
    
    @patch('subprocess.run')
    def test_claude_with_model_selection(self, mock_run):
        """Test claude with specific model selection."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # --version check
            MagicMock(
                returncode=0,
                stdout="Test response from Opus",
                stderr="Tokens: 50"
            )
        ]
        
        response = self.adapter.execute(
            self.test_prompt,
            model="claude-3-opus",
            dangerously_skip_permissions=True
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.metadata["model"], "claude-3-opus")
        
        # Verify model parameter was passed
        actual_call = mock_run.call_args_list[1]
        cmd = actual_call[0][0]
        self.assertIn("--model", cmd)
        self.assertIn("claude-3-opus", cmd)
        self.assertIn("--dangerously-skip-permissions", cmd)
    
    @patch('subprocess.run')
    def test_claude_json_output(self, mock_run):
        """Test claude with JSON output format."""
        json_response = {
            "answer": "Recursion is when a function calls itself.",
            "confidence": 0.95
        }
        
        mock_run.side_effect = [
            MagicMock(returncode=0),  # --version check
            MagicMock(
                returncode=0,
                stdout=json.dumps(json_response),
                stderr="Tokens: 30"
            )
        ]
        
        response = self.adapter.execute(
            self.test_prompt,
            output_format="json"
        )
        
        self.assertTrue(response.success)
        # Parse JSON to verify it's valid
        parsed = json.loads(response.output)
        self.assertEqual(parsed["confidence"], 0.95)
        
        # Verify output format parameter
        actual_call = mock_run.call_args_list[1]
        cmd = actual_call[0][0]
        self.assertIn("--output-format", cmd)
        self.assertIn("json", cmd)
    
    @patch('subprocess.run')
    def test_claude_rate_limit_error(self, mock_run):
        """Test claude rate limit error handling."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # --version check
            MagicMock(
                returncode=1,
                stdout="",
                stderr="Error: Rate limit exceeded. Please wait 60 seconds."
            )
        ]
        
        response = self.adapter.execute(self.test_prompt)
        
        self.assertFalse(response.success)
        self.assertIn("Rate limit", response.error)
    
    def test_claude_token_extraction(self):
        """Test token extraction from various stderr formats."""
        test_cases = [
            ("Tokens used: 150", 150),
            ("Total tokens: 200", 200),
            ("Used 300 tokens", 300),
            ("tokens:500", 500),
            ("No token info here", None)
        ]
        
        for stderr, expected in test_cases:
            result = self.adapter._extract_token_count(stderr)
            self.assertEqual(result, expected, f"Failed for: {stderr}")
    
    def test_claude_cost_calculation(self):
        """Test Claude cost calculation."""
        # Test with known token counts
        cost_100_tokens = self.adapter._calculate_cost(100)
        cost_1000_tokens = self.adapter._calculate_cost(1000)
        cost_10000_tokens = self.adapter._calculate_cost(10000)
        
        self.assertGreater(cost_1000_tokens, cost_100_tokens)
        self.assertGreater(cost_10000_tokens, cost_1000_tokens)
        self.assertAlmostEqual(cost_1000_tokens, 0.009, places=3)


class TestOrchestratorIntegration(unittest.TestCase):
    """Integration tests for the full orchestrator."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.prompt_file = Path(self.temp_dir) / "PROMPT.md"
        self.prompt_file.write_text("Test prompt content")
        
        # Change to temp directory for git operations
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], capture_output=True)
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('ralph_orchestrator.adapters.claude.subprocess.run')
    @patch('ralph_orchestrator.adapters.qchat.subprocess.run')
    def test_orchestrator_with_qchat_primary(self, mock_qchat_run, mock_claude_run):
        """Test orchestrator with q chat as primary tool."""
        # Mock tool availability
        mock_qchat_run.side_effect = [
            MagicMock(returncode=0),  # which q
            MagicMock(
                returncode=0,
                stdout="Q Chat response iteration 1",
                stderr=""
            ),
            MagicMock(returncode=0),  # Second iteration which q
            MagicMock(
                returncode=0,
                stdout="TASK_COMPLETE",
                stderr=""
            )
        ]
        
        mock_claude_run.return_value = MagicMock(returncode=1)  # Claude not available
        
        orchestrator = RalphOrchestrator(
            prompt_file=str(self.prompt_file),
            primary_tool="qchat",
            max_iterations=5
        )
        
        # Run orchestrator
        orchestrator.run()
        
        # Verify execution
        self.assertGreater(orchestrator.metrics.iterations, 0)
        self.assertGreater(orchestrator.metrics.successful_iterations, 0)
    
    @patch('ralph_orchestrator.adapters.claude.subprocess.run')
    @patch('ralph_orchestrator.adapters.qchat.subprocess.run')
    def test_orchestrator_fallback_chain(self, mock_qchat_run, mock_claude_run):
        """Test orchestrator fallback from q chat to claude."""
        # Q chat fails
        mock_qchat_run.side_effect = [
            MagicMock(returncode=0),  # which q - available
            MagicMock(returncode=1, stdout="", stderr="Q chat error"),  # Execution fails
            MagicMock(returncode=0),  # Second iteration check
            MagicMock(returncode=1, stdout="", stderr="Q chat error"),  # Still fails
        ]
        
        # Claude succeeds
        mock_claude_run.side_effect = [
            MagicMock(returncode=0),  # --version check
            MagicMock(
                returncode=0,
                stdout="Claude fallback response",
                stderr="Tokens: 50"
            ),
            MagicMock(returncode=0),  # Second iteration version check
            MagicMock(
                returncode=0,
                stdout="TASK_COMPLETE",
                stderr="Tokens: 20"
            )
        ]
        
        orchestrator = RalphOrchestrator(
            prompt_file=str(self.prompt_file),
            primary_tool="qchat",
            max_iterations=5
        )
        
        orchestrator.run()
        
        # Should have successful iterations despite primary tool failure
        self.assertGreater(orchestrator.metrics.successful_iterations, 0)
    
    @patch('ralph_orchestrator.adapters.claude.subprocess.run')
    def test_orchestrator_with_cost_tracking(self, mock_claude_run):
        """Test orchestrator with cost tracking enabled."""
        mock_claude_run.side_effect = [
            MagicMock(returncode=0),  # --version
            MagicMock(
                returncode=0,
                stdout="Response 1",
                stderr="Tokens: 100"
            ),
            MagicMock(returncode=0),  # Second iteration
            MagicMock(
                returncode=0,
                stdout="TASK_COMPLETE",
                stderr="Tokens: 50"
            )
        ]
        
        orchestrator = RalphOrchestrator(
            prompt_file=str(self.prompt_file),
            primary_tool="claude",
            track_costs=True,
            max_cost=1.0,
            max_iterations=5
        )
        
        orchestrator.run()
        
        # Verify cost tracking
        self.assertIsNotNone(orchestrator.cost_tracker)
        self.assertGreater(orchestrator.cost_tracker.total_cost, 0)
        self.assertIn("claude", orchestrator.cost_tracker.costs_by_tool)
    
    @patch('ralph_orchestrator.adapters.claude.subprocess.run')
    def test_orchestrator_safety_limits(self, mock_claude_run):
        """Test orchestrator safety limits."""
        # Mock endless responses (never complete)
        mock_claude_run.return_value = MagicMock(
            returncode=0,
            stdout="Still working...",
            stderr="Tokens: 10"
        )
        
        orchestrator = RalphOrchestrator(
            prompt_file=str(self.prompt_file),
            primary_tool="claude",
            max_iterations=3,  # Very low limit
            max_runtime=5  # 5 seconds max
        )
        
        start_time = time.time()
        orchestrator.run()
        elapsed = time.time() - start_time
        
        # Should stop due to iteration limit
        self.assertEqual(orchestrator.metrics.iterations, 3)
        self.assertLess(elapsed, 30)  # Should not run forever
    
    @patch('subprocess.run')
    def test_orchestrator_checkpoint_creation(self, mock_run):
        """Test orchestrator git checkpoint creation."""
        # Create a more complete mock sequence
        mock_run.side_effect = [
            # Initial git operations
            MagicMock(returncode=0),  # git add
            MagicMock(returncode=0),  # git commit
            # Tool checks and executions would go here
            MagicMock(returncode=1),  # Tool not available
        ]
        
        orchestrator = RalphOrchestrator(
            prompt_file=str(self.prompt_file),
            primary_tool="claude",
            checkpoint_interval=1  # Checkpoint every iteration
        )
        
        # Manually trigger checkpoint
        orchestrator._create_checkpoint()
        
        # Verify git commands were called
        calls = mock_run.call_args_list
        git_add_called = any("git" in str(call) and "add" in str(call) for call in calls)
        self.assertTrue(git_add_called)


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests with multiple tools."""
    
    @patch('subprocess.run')
    def test_complete_workflow_with_all_tools(self, mock_run):
        """Test complete workflow with all three tools."""
        temp_dir = tempfile.mkdtemp()
        prompt_file = Path(temp_dir) / "PROMPT.md"
        prompt_file.write_text("Generate a Python function to sort a list")
        
        # Mock all tool responses in sequence
        mock_run.side_effect = [
            # Git init
            MagicMock(returncode=0),
            MagicMock(returncode=0),
            MagicMock(returncode=0),
            
            # Tool availability checks
            MagicMock(returncode=0),  # claude --version
            MagicMock(returncode=0),  # which q
            MagicMock(returncode=0),  # gemini --version
            
            # First iteration - q chat succeeds
            MagicMock(
                returncode=0,
                stdout="def sort_list(lst):\n    return sorted(lst)",
                stderr=""
            ),
            
            # Git checkpoint
            MagicMock(returncode=0),  # git add
            MagicMock(returncode=0),  # git commit
            
            # Check for completion (mock reading file with TASK_COMPLETE)
        ]
        
        os.chdir(temp_dir)
        subprocess.run(["git", "init"], capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], capture_output=True)
        
        orchestrator = RalphOrchestrator(
            prompt_file=str(prompt_file),
            primary_tool="qchat",
            max_iterations=2,
            checkpoint_interval=1
        )
        
        # Update prompt to mark complete
        prompt_file.write_text("TASK_COMPLETE")
        
        orchestrator.run()
        
        # Verify successful execution
        self.assertGreater(orchestrator.metrics.iterations, 0)
        
        # Cleanup
        os.chdir("/tmp")
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()