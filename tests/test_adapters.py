# ABOUTME: Test suite for Ralph Orchestrator adapters
# ABOUTME: Validates that adapters can be initialized and checked for availability

"""Tests for Ralph Orchestrator adapters."""

import unittest
from unittest.mock import patch, MagicMock
import subprocess

from ralph_orchestrator.adapters.base import ToolAdapter, ToolResponse
from ralph_orchestrator.adapters.claude import ClaudeAdapter
from ralph_orchestrator.adapters.qchat import QChatAdapter
from ralph_orchestrator.adapters.gemini import GeminiAdapter


class TestToolResponse(unittest.TestCase):
    """Test ToolResponse dataclass."""
    
    def test_tool_response_creation(self):
        """Test creating a tool response."""
        response = ToolResponse(
            success=True,
            output="Test output",
            tokens_used=100,
            cost=0.001
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.output, "Test output")
        self.assertEqual(response.tokens_used, 100)
        self.assertEqual(response.cost, 0.001)
    
    def test_tool_response_with_error(self):
        """Test creating an error response."""
        response = ToolResponse(
            success=False,
            output="",
            error="Command failed"
        )
        
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Command failed")


class TestClaudeAdapter(unittest.TestCase):
    """Test Claude adapter."""
    
    @patch('subprocess.run')
    def test_check_availability_success(self, mock_run):
        """Test Claude availability check when available."""
        mock_run.return_value = MagicMock(returncode=0)
        
        adapter = ClaudeAdapter()
        self.assertTrue(adapter.available)
    
    @patch('subprocess.run')
    def test_check_availability_failure(self, mock_run):
        """Test Claude availability check when not available."""
        mock_run.side_effect = FileNotFoundError()
        
        adapter = ClaudeAdapter()
        self.assertFalse(adapter.available)
    
    @patch('subprocess.run')
    def test_execute_success(self, mock_run):
        """Test successful Claude execution."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # availability check
            MagicMock(
                returncode=0,
                stdout="Claude response",
                stderr=""
            )  # execution
        ]
        
        adapter = ClaudeAdapter()
        response = adapter.execute("Test prompt")
        
        self.assertTrue(response.success)
        self.assertEqual(response.output, "Claude response")
    
    def test_estimate_cost(self):
        """Test cost estimation."""
        adapter = ClaudeAdapter()
        
        # Test with 1000 character prompt (roughly 250 tokens)
        cost = adapter.estimate_cost("x" * 1000)
        self.assertGreater(cost, 0)


class TestQChatAdapter(unittest.TestCase):
    """Test Q Chat adapter."""
    
    @patch('subprocess.run')
    def test_check_availability_success(self, mock_run):
        """Test Q Chat availability check when available."""
        mock_run.return_value = MagicMock(returncode=0)
        
        adapter = QChatAdapter()
        # Note: availability check uses 'which q'
        mock_run.assert_called_with(
            ["which", "q"],
            capture_output=True,
            timeout=5,
            text=True
        )
    
    @patch('subprocess.run')
    def test_execute_success(self, mock_run):
        """Test successful Q Chat execution."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # availability check
            MagicMock(
                returncode=0,
                stdout="Q Chat response",
                stderr=""
            )  # execution
        ]
        
        adapter = QChatAdapter()
        response = adapter.execute("Test prompt")
        
        self.assertTrue(response.success)
        self.assertEqual(response.output, "Q Chat response")
    
    def test_estimate_cost(self):
        """Test Q Chat cost estimation (should be free)."""
        adapter = QChatAdapter()
        cost = adapter.estimate_cost("Any prompt")
        self.assertEqual(cost, 0.0)


class TestGeminiAdapter(unittest.TestCase):
    """Test Gemini adapter."""
    
    @patch('subprocess.run')
    def test_check_availability_success(self, mock_run):
        """Test Gemini availability check when available."""
        mock_run.return_value = MagicMock(returncode=0)
        
        adapter = GeminiAdapter()
        self.assertTrue(adapter.available)
    
    @patch('subprocess.run')
    def test_execute_with_model(self, mock_run):
        """Test Gemini execution with custom model."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # availability check
            MagicMock(
                returncode=0,
                stdout="Gemini response",
                stderr=""
            )  # execution
        ]
        
        adapter = GeminiAdapter()
        response = adapter.execute("Test prompt", model="gemini-pro")
        
        self.assertTrue(response.success)
        self.assertEqual(response.output, "Gemini response")
        self.assertEqual(response.metadata["model"], "gemini-pro")
    
    def test_free_tier_cost(self):
        """Test Gemini free tier cost calculation."""
        adapter = GeminiAdapter()
        
        # Under 1M tokens should be free
        cost = adapter._calculate_cost(500000)
        self.assertEqual(cost, 0.0)
        
        # Over 1M tokens should have cost
        cost = adapter._calculate_cost(2000000)
        self.assertGreater(cost, 0)


if __name__ == "__main__":
    unittest.main()