#!/usr/bin/env python3
# ABOUTME: Comprehensive test suite for Ralph orchestrator production readiness
# ABOUTME: Tests all critical features including security, monitoring, and limits

import unittest
import tempfile
import json
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ralph_orchestrator import (
    RalphConfig, RalphOrchestrator, AgentType, TokenMetrics,
    ContextManager, MetricsCollector, SecurityValidator
)

class TestTokenMetrics(unittest.TestCase):
    """Test token and cost tracking functionality"""
    
    def test_token_tracking(self):
        metrics = TokenMetrics()
        metrics.add_iteration(1000, 500, "claude")
        
        self.assertEqual(metrics.input_tokens, 1000)
        self.assertEqual(metrics.output_tokens, 500)
        self.assertEqual(metrics.get_total_tokens(), 1500)
        self.assertGreater(metrics.total_cost, 0)
    
    def test_cost_calculation(self):
        metrics = TokenMetrics()
        # Claude costs: $3/1M input, $15/1M output
        metrics.add_iteration(1_000_000, 1_000_000, "claude")
        
        expected_cost = 3.0 + 15.0  # $18 total
        self.assertAlmostEqual(metrics.total_cost, expected_cost, places=2)
    
    def test_limit_checking(self):
        metrics = TokenMetrics()
        metrics.add_iteration(500_000, 200_000, "claude")
        
        # Should be within limits
        self.assertTrue(metrics.is_within_limits(1_000_000, 50.0))
        
        # Should exceed token limit
        self.assertFalse(metrics.is_within_limits(100_000, 50.0))
        
        # Should exceed cost limit
        self.assertFalse(metrics.is_within_limits(10_000_000, 1.0))

class TestContextManager(unittest.TestCase):
    """Test context window management"""
    
    def test_token_estimation(self):
        manager = ContextManager(200_000, 0.8)
        
        # Roughly 1 token per 4 characters
        text = "a" * 4000
        tokens = manager.estimate_tokens(text)
        self.assertAlmostEqual(tokens, 1000, delta=100)
    
    def test_summarization_trigger(self):
        manager = ContextManager(10_000, 0.8)
        
        # Small prompt - no summarization needed
        small_prompt = "Short prompt"
        self.assertFalse(manager.needs_summarization(small_prompt))
        
        # Large prompt - summarization needed
        large_prompt = "x" * 40_000  # ~10K tokens
        self.assertTrue(manager.needs_summarization(large_prompt))
    
    def test_prompt_history(self):
        manager = ContextManager(200_000, 0.8)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Test prompt content")
            prompt_path = Path(f.name)
        
        try:
            manager.add_to_history(prompt_path)
            self.assertEqual(len(manager.prompt_history), 1)
            self.assertIn('hash', manager.prompt_history[0])
            self.assertIn('tokens', manager.prompt_history[0])
        finally:
            prompt_path.unlink()

class TestSecurityValidator(unittest.TestCase):
    """Test security validation and sanitization"""
    
    def test_safe_prompt_validation(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Write a simple Python function")
            prompt_path = Path(f.name)
        
        try:
            is_valid, error = SecurityValidator.validate_prompt_file(
                prompt_path, 10_000_000, allow_unsafe=False
            )
            self.assertTrue(is_valid)
            self.assertIsNone(error)
        finally:
            prompt_path.unlink()
    
    def test_unsafe_prompt_detection(self):
        unsafe_contents = [
            "$(rm -rf /)",
            "`cat /etc/passwd`",
            "test | sh",
            "../../etc/passwd"
        ]
        
        for content in unsafe_contents:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(content)
                prompt_path = Path(f.name)
            
            try:
                is_valid, error = SecurityValidator.validate_prompt_file(
                    prompt_path, 10_000_000, allow_unsafe=False
                )
                self.assertFalse(is_valid, f"Failed to detect: {content}")
                self.assertIsNotNone(error)
            finally:
                prompt_path.unlink()
    
    def test_file_size_limit(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("x" * 1000)
            prompt_path = Path(f.name)
        
        try:
            # Should fail with small limit
            is_valid, error = SecurityValidator.validate_prompt_file(
                prompt_path, 100, allow_unsafe=False
            )
            self.assertFalse(is_valid)
            self.assertIn("too large", error.lower())
        finally:
            prompt_path.unlink()
    
    def test_command_sanitization(self):
        args = ["test", "$(echo pwned)", "normal arg"]
        sanitized = SecurityValidator.sanitize_command_args(args)
        
        # Should be properly quoted
        self.assertEqual(len(sanitized), 3)
        self.assertIn("'", sanitized[1])  # Should be quoted

class TestMetricsCollector(unittest.TestCase):
    """Test metrics collection and reporting"""
    
    def test_metrics_recording(self):
        collector = MetricsCollector(enabled=True)
        
        collector.record_iteration_metrics(
            iteration=1,
            duration=5.0,
            tokens=1000,
            cost=0.5,
            success=True
        )
        
        self.assertEqual(len(collector.metrics_history), 1)
        metric = collector.metrics_history[0]
        self.assertEqual(metric['iteration'], 1)
        self.assertEqual(metric['duration_seconds'], 5.0)
        self.assertTrue(metric['success'])
    
    def test_metrics_summary(self):
        collector = MetricsCollector(enabled=True)
        
        # Record multiple iterations
        for i in range(3):
            collector.record_iteration_metrics(
                iteration=i+1,
                duration=10.0,
                tokens=500,
                cost=0.25,
                success=(i != 1)  # Second iteration fails
            )
        
        summary = collector.get_summary()
        self.assertEqual(summary['total_iterations'], 3)
        self.assertEqual(summary['successful_iterations'], 2)
        self.assertAlmostEqual(summary['success_rate'], 0.667, places=2)
        self.assertEqual(summary['total_duration_seconds'], 30.0)
        self.assertEqual(summary['total_tokens'], 1500)

class TestRalphOrchestrator(unittest.TestCase):
    """Test main orchestrator functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.prompt_file = Path(self.temp_dir) / "test_prompt.md"
        self.prompt_file.write_text("Test prompt content")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        config = RalphConfig(
            agent=AgentType.Q,
            prompt_file=str(self.prompt_file),
            max_iterations=10
        )
        
        orchestrator = RalphOrchestrator(config)
        self.assertEqual(orchestrator.config.agent, AgentType.Q)
        self.assertEqual(orchestrator.iteration_count, 0)
        self.assertIsNotNone(orchestrator.token_metrics)
        self.assertIsNotNone(orchestrator.context_manager)
        self.assertIsNotNone(orchestrator.metrics_collector)
    
    @patch('subprocess.run')
    def test_agent_detection(self, mock_run):
        config = RalphConfig(
            agent=AgentType.AUTO,
            prompt_file=str(self.prompt_file)
        )
        
        # Mock q being available
        mock_run.return_value = Mock(returncode=0)
        
        orchestrator = RalphOrchestrator(config)
        detected = orchestrator.detect_agent()
        
        # Should detect claude (first in list)
        self.assertEqual(detected, AgentType.CLAUDE)
    
    def test_completion_detection(self):
        config = RalphConfig(
            agent=AgentType.Q,
            prompt_file=str(self.prompt_file)
        )
        
        orchestrator = RalphOrchestrator(config)
        
        # Initially not complete
        self.assertFalse(orchestrator.check_completion())
        
        # Add completion marker
        self.prompt_file.write_text("Test prompt\nTASK_COMPLETE")
        self.assertTrue(orchestrator.check_completion())
    
    def test_should_continue_limits(self):
        config = RalphConfig(
            agent=AgentType.Q,
            prompt_file=str(self.prompt_file),
            max_iterations=5,
            max_runtime=100
        )
        
        orchestrator = RalphOrchestrator(config)
        
        # Should continue initially
        self.assertTrue(orchestrator.should_continue())
        
        # Exceed iteration limit
        orchestrator.iteration_count = 5
        self.assertFalse(orchestrator.should_continue())
        
        # Reset and exceed runtime
        orchestrator.iteration_count = 0
        orchestrator.start_time = 0  # Very old start time
        self.assertFalse(orchestrator.should_continue())
    
    def test_state_saving(self):
        config = RalphConfig(
            agent=AgentType.Q,
            prompt_file=str(self.prompt_file)
        )
        
        orchestrator = RalphOrchestrator(config)
        orchestrator.iteration_count = 3
        orchestrator.token_metrics.add_iteration(100, 50, "q")
        
        orchestrator.save_state()
        
        # Check state file was created
        state_files = list(Path(".agent/metrics").glob("state_*.json"))
        self.assertGreater(len(state_files), 0)
        
        # Load and verify state
        with open(state_files[-1]) as f:
            state = json.load(f)
        
        self.assertEqual(state['iteration_count'], 3)
        self.assertEqual(state['token_metrics']['input_tokens'], 100)
        self.assertEqual(state['token_metrics']['output_tokens'], 50)

class TestIntegration(unittest.TestCase):
    """Integration tests for full workflow"""
    
    @patch('subprocess.run')
    def test_full_iteration_cycle(self, mock_run):
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = Path(temp_dir) / "prompt.md"
            prompt_file.write_text("Test task")
            
            config = RalphConfig(
                agent=AgentType.Q,
                prompt_file=str(prompt_file),
                max_iterations=1,
                dry_run=False
            )
            
            # Mock successful agent execution
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Task completed",
                stderr=""
            )
            
            orchestrator = RalphOrchestrator(config)
            
            # Run iteration
            result = orchestrator.run_iteration()
            
            # Should have called subprocess
            mock_run.assert_called_once()
            
            # Should have recorded metrics
            self.assertEqual(orchestrator.iteration_count, 1)
            self.assertGreater(orchestrator.token_metrics.get_total_tokens(), 0)

if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)