#!/usr/bin/env python3
# ABOUTME: Comprehensive test suite for ralph-orchestrator with all features
# ABOUTME: Tests agents, fallback chains, checkpointing, and error recovery

import unittest
import subprocess
import tempfile
import json
import time
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ralph_orchestrator import RalphOrchestrator, RalphConfig, AgentType

class TestRalphOrchestrator(unittest.TestCase):
    """Comprehensive test suite for Ralph orchestrator"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test prompt file
        self.prompt_file = Path("PROMPT.md")
        self.prompt_file.write_text("Test prompt content")
        
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_agent_detection(self):
        """Test auto-detection of available agents"""
        config = RalphConfig(agent=AgentType.AUTO)
        orchestrator = RalphOrchestrator(config)
        
        # Mock subprocess to simulate agent availability
        with patch('subprocess.run') as mock_run:
            # Simulate claude being available
            mock_run.return_value = MagicMock(returncode=0)
            agent = orchestrator.detect_agent()
            self.assertEqual(agent, AgentType.CLAUDE)
    
    def test_build_claude_command(self):
        """Test command building for Claude agent"""
        config = RalphConfig(agent=AgentType.CLAUDE, prompt_file="PROMPT.md")
        orchestrator = RalphOrchestrator(config)
        
        cmd = orchestrator.build_agent_command()
        self.assertEqual(cmd, ["claude", "-p", "@PROMPT.md"])
    
    def test_build_q_command(self):
        """Test command building for q chat agent"""
        config = RalphConfig(agent=AgentType.Q, prompt_file="PROMPT.md")
        orchestrator = RalphOrchestrator(config)
        
        cmd = orchestrator.build_agent_command()
        self.assertIn("q", cmd)
        self.assertIn("chat", cmd)
        self.assertIn("--no-interactive", cmd)
        self.assertIn("--trust-all-tools", cmd)
    
    def test_checkpoint_creation(self):
        """Test checkpoint creation functionality"""
        config = RalphConfig(
            agent=AgentType.CLAUDE,
            archive_prompts=True,
            git_checkpoint=False  # Disable git for testing
        )
        orchestrator = RalphOrchestrator(config)
        orchestrator.iteration_count = 5
        
        # Create checkpoint
        orchestrator.create_checkpoint()
        
        # Check if prompt was archived
        archive_path = Path(f".agent/prompts/prompt_0005.md")
        self.assertTrue(archive_path.exists())
        self.assertEqual(archive_path.read_text(), "Test prompt content")
    
    def test_completion_detection(self):
        """Test task completion detection"""
        config = RalphConfig(agent=AgentType.CLAUDE)
        orchestrator = RalphOrchestrator(config)
        
        # Test not complete
        self.assertFalse(orchestrator.check_completion())
        
        # Mark as complete
        self.prompt_file.write_text("Test prompt\nTASK_COMPLETE")
        self.assertTrue(orchestrator.check_completion())
    
    def test_error_handling(self):
        """Test error handling and recovery"""
        config = RalphConfig(
            agent=AgentType.CLAUDE,
            retry_delay=0.1,
            max_iterations=3
        )
        orchestrator = RalphOrchestrator(config)
        
        # Simulate failed agent execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Error message"
            )
            
            result = orchestrator.run_iteration()
            self.assertFalse(result)
            self.assertEqual(len(orchestrator.errors), 1)
    
    def test_state_persistence(self):
        """Test state saving and loading"""
        config = RalphConfig(agent=AgentType.CLAUDE)
        orchestrator = RalphOrchestrator(config)
        orchestrator.iteration_count = 10
        orchestrator.errors = [{"iteration": 5, "error": "test"}]
        
        # Save state
        orchestrator.save_state()
        
        # Check if state file exists
        state_files = list(Path(".agent/metrics").glob("state_*.json"))
        self.assertGreater(len(state_files), 0)
        
        # Load and verify state
        with open(state_files[0]) as f:
            state = json.load(f)
            self.assertEqual(state["iteration_count"], 10)
            self.assertEqual(len(state["errors"]), 1)
    
    def test_max_iterations_limit(self):
        """Test max iterations limit enforcement"""
        config = RalphConfig(
            agent=AgentType.CLAUDE,
            max_iterations=2
        )
        orchestrator = RalphOrchestrator(config)
        orchestrator.iteration_count = 2
        
        self.assertFalse(orchestrator.should_continue())
    
    def test_max_runtime_limit(self):
        """Test max runtime limit enforcement"""
        config = RalphConfig(
            agent=AgentType.CLAUDE,
            max_runtime=1  # 1 second
        )
        orchestrator = RalphOrchestrator(config)
        orchestrator.start_time = time.time() - 2  # Started 2 seconds ago
        
        self.assertFalse(orchestrator.should_continue())
    
    def test_consecutive_error_limit(self):
        """Test stopping after too many consecutive errors"""
        config = RalphConfig(agent=AgentType.CLAUDE)
        orchestrator = RalphOrchestrator(config)
        
        # Add 5 consecutive errors
        orchestrator.iteration_count = 10
        for i in range(5):
            orchestrator.errors.append({
                'iteration': orchestrator.iteration_count - 4 + i,
                'error': f'Error {i}'
            })
        
        self.assertFalse(orchestrator.should_continue())
    
    def test_dry_run_mode(self):
        """Test dry run mode doesn't execute agents"""
        config = RalphConfig(
            agent=AgentType.CLAUDE,
            dry_run=True
        )
        orchestrator = RalphOrchestrator(config)
        
        with patch('subprocess.run') as mock_run:
            result = orchestrator.run_iteration()
            self.assertTrue(result)
            mock_run.assert_not_called()
    
    def test_additional_agent_args(self):
        """Test passing additional arguments to agents"""
        config = RalphConfig(
            agent=AgentType.CLAUDE,
            agent_args=["--model", "claude-3-opus"]
        )
        orchestrator = RalphOrchestrator(config)
        
        cmd = orchestrator.build_agent_command()
        self.assertIn("--model", cmd)
        self.assertIn("claude-3-opus", cmd)
    
    def test_directory_creation(self):
        """Test that necessary directories are created"""
        config = RalphConfig(agent=AgentType.CLAUDE)
        orchestrator = RalphOrchestrator(config)
        
        # Check all required directories exist
        self.assertTrue(Path(".agent").exists())
        self.assertTrue(Path(".agent/prompts").exists())
        self.assertTrue(Path(".agent/checkpoints").exists())
        self.assertTrue(Path(".agent/metrics").exists())

class TestIntegration(unittest.TestCase):
    """Integration tests with real agents"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        """Clean up integration test environment"""
        os.chdir(self.original_dir)
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_end_to_end_with_mock_agent(self):
        """Test end-to-end flow with mocked agent"""
        # Create test prompt
        Path("PROMPT.md").write_text("Test task")
        
        config = RalphConfig(
            agent=AgentType.CLAUDE,
            max_iterations=2,
            dry_run=False
        )
        
        with patch('subprocess.run') as mock_run:
            # First iteration: task not complete
            mock_run.return_value = MagicMock(returncode=0, stdout="Working...")
            
            orchestrator = RalphOrchestrator(config)
            result = orchestrator.run_iteration()
            self.assertIsNone(result)  # Should continue
            
            # Second iteration: mark complete
            Path("PROMPT.md").write_text("Test task\nTASK_COMPLETE")
            result = orchestrator.run_iteration()
            self.assertTrue(result)  # Should complete
    
    def test_fallback_chain(self):
        """Test fallback between different agents"""
        Path("PROMPT.md").write_text("Test task")
        
        config = RalphConfig(agent=AgentType.AUTO)
        
        with patch('subprocess.run') as mock_run:
            # First call: version check for claude fails
            # Second call: version check for q succeeds
            # Third call: q execution succeeds
            mock_run.side_effect = [
                MagicMock(returncode=1),  # claude --version fails
                MagicMock(returncode=0),  # q --version succeeds
                MagicMock(returncode=0, stdout="Success")  # q execution
            ]
            
            orchestrator = RalphOrchestrator(config)
            agent = orchestrator.detect_agent()
            self.assertEqual(agent, AgentType.Q)

class TestCLI(unittest.TestCase):
    """Test command-line interface"""
    
    def test_cli_help(self):
        """Test CLI help output"""
        result = subprocess.run(
            ["python", "ralph_orchestrator.py", "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Ralph Wiggum Orchestrator", result.stdout)
    
    def test_cli_with_args(self):
        """Test CLI with various arguments"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prompt_file = Path(tmpdir) / "test.md"
            prompt_file.write_text("Test prompt\nTASK_COMPLETE")
            
            result = subprocess.run(
                [
                    "python", os.path.join(os.path.dirname(__file__), "ralph_orchestrator.py"),
                    "--agent", "claude",
                    "--prompt", str(prompt_file),
                    "--max-iterations", "1",
                    "--dry-run"
                ],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )
            
            self.assertIn("Task completed successfully", result.stderr)

if __name__ == "__main__":
    unittest.main()