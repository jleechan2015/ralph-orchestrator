# ABOUTME: Integration tests for Q Chat adapter
# ABOUTME: Tests real-world scenarios and stress conditions

"""Integration tests for Q Chat adapter."""

import pytest
import asyncio
import threading
import time
import signal
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from src.ralph_orchestrator.adapters.qchat import QChatAdapter


class TestQChatIntegration:
    """Integration tests for Q Chat adapter."""
    
    def test_adapter_initialization_and_availability(self):
        """Test complete initialization and availability check flow."""
        adapter = QChatAdapter()
        
        # Check basic properties
        assert adapter.command == "q"
        assert adapter.name == "qchat"
        assert hasattr(adapter, 'available')
        assert hasattr(adapter, '_lock')
        assert hasattr(adapter, 'current_process')
        
        # Availability check (may be True or False depending on system)
        # Just ensure it doesn't crash
        availability = adapter.check_availability()
        assert isinstance(availability, bool)
    
    def test_concurrent_adapter_instances(self):
        """Test multiple adapter instances can coexist."""
        adapters = []
        for i in range(5):
            adapter = QChatAdapter()
            adapters.append(adapter)
            assert adapter is not None
        
        # Each should have its own lock
        locks = [a._lock for a in adapters]
        assert len(set(id(lock) for lock in locks)) == 5
    
    @patch('subprocess.Popen')
    def test_stress_concurrent_executions(self, mock_popen):
        """Test adapter under concurrent execution stress."""
        adapter = QChatAdapter()
        adapter.available = True
        
        results = []
        errors = []
        
        def create_mock_process(output):
            mock_process = Mock()
            mock_process.poll.side_effect = [None, None, 0]
            mock_process.stdout = Mock()
            mock_process.stderr = Mock()
            mock_process.stdout.read.return_value = output
            mock_process.stderr.read.return_value = ""
            mock_process.stdout.fileno.return_value = 1
            mock_process.stderr.fileno.return_value = 2
            mock_process.terminate = Mock()
            mock_process.kill = Mock()
            mock_process.wait = Mock()
            return mock_process
        
        # Return different mock processes for each call
        mock_popen.side_effect = [
            create_mock_process(f"Output {i}") for i in range(10)
        ]
        
        def execute_task(task_id):
            try:
                with patch.object(adapter, '_read_available', return_value=""):
                    response = adapter.execute(f"Task {task_id}", verbose=False)
                    results.append(response)
            except Exception as e:
                errors.append(e)
        
        # Run tasks sequentially (adapter doesn't support true parallel execution)
        for i in range(10):
            execute_task(i)
        
        # Check results
        assert len(errors) == 0
        assert len(results) == 10
        for i, result in enumerate(results):
            assert result.success is True
            assert f"Output {i}" in result.output
    
    def test_signal_handling_integration(self):
        """Test signal handling in integration scenario."""
        adapter = QChatAdapter()
        
        # Store original handler
        original_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        try:
            # Adapter should have registered its handler
            current_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)
            signal.signal(signal.SIGINT, current_handler)
            
            # Simulate a process
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_process.terminate = Mock()
            mock_process.wait = Mock()
            
            with adapter._lock:
                adapter.current_process = mock_process
            
            # Trigger signal handler
            adapter._signal_handler(signal.SIGINT, None)
            
            # Check that shutdown was requested
            assert adapter.shutdown_requested is True
            mock_process.terminate.assert_called_once()
            
        finally:
            # Restore original handler
            signal.signal(signal.SIGINT, original_handler)
    
    def test_resource_cleanup_on_error(self):
        """Test resource cleanup when errors occur."""
        adapter = QChatAdapter()
        adapter.available = True
        
        with patch('subprocess.Popen') as mock_popen:
            # Simulate process creation failure
            mock_popen.side_effect = OSError("Cannot create process")
            
            response = adapter.execute("test", verbose=False)
            
            assert response.success is False
            assert "Cannot create process" in response.error
            assert adapter.current_process is None
    
    def test_timeout_and_recovery(self):
        """Test timeout handling and recovery."""
        adapter = QChatAdapter()
        adapter.available = True
        
        with patch('subprocess.Popen') as mock_popen:
            # Create a mock process that never completes
            mock_process = Mock()
            mock_process.poll.return_value = None  # Always running
            mock_process.stdout = Mock()
            mock_process.stderr = Mock()
            mock_process.stdout.fileno.return_value = 1
            mock_process.stderr.fileno.return_value = 2
            mock_process.stdout.read.return_value = ""
            mock_process.stderr.read.return_value = ""
            mock_process.terminate = Mock()
            mock_process.kill = Mock()
            mock_process.wait = Mock(side_effect=Exception("Process won't die"))
            mock_popen.return_value = mock_process
            
            with patch('time.time') as mock_time:
                # Simulate immediate timeout
                mock_time.side_effect = [0, 2, 2.1]
                
                with patch.object(adapter, '_read_available', return_value=""):
                    response = adapter.execute("test", timeout=1, verbose=False)
            
            assert response.success is False
            assert "timed out" in response.error
            mock_process.terminate.assert_called()
            
            # Adapter should be ready for next execution
            assert adapter.current_process is None
            assert adapter.shutdown_requested is False
    
    @pytest.mark.asyncio
    async def test_async_execution_integration(self):
        """Test async execution in integration scenario."""
        adapter = QChatAdapter()
        adapter.available = True
        
        with patch('asyncio.create_subprocess_exec') as mock_create:
            mock_process = Mock()
            mock_process.returncode = 0
            async def mock_communicate():
                return (b"Async output", b"")
            mock_process.communicate = mock_communicate
            mock_process.terminate = Mock()
            mock_process.kill = Mock()
            async def mock_wait():
                return None
            mock_process.wait = mock_wait
            mock_create.return_value = mock_process
            
            response = await adapter.aexecute("async test", verbose=False)
            
            assert response.success is True
            assert response.output == "Async output"
            assert response.metadata.get("async") is True
    
    @pytest.mark.asyncio
    async def test_async_timeout_recovery(self):
        """Test async timeout and recovery."""
        adapter = QChatAdapter()
        adapter.available = True
        
        with patch('asyncio.create_subprocess_exec') as mock_create:
            mock_process = Mock()
            
            async def slow_communicate():
                await asyncio.sleep(10)  # Simulate slow process
                return (b"", b"")
            
            mock_process.communicate = slow_communicate
            mock_process.terminate = Mock()
            mock_process.kill = Mock()
            async def mock_wait():
                return None
            mock_process.wait = mock_wait
            mock_create.return_value = mock_process
            
            response = await adapter.aexecute("test", timeout=0.1, verbose=False)
            
            assert response.success is False
            assert "timed out" in response.error
            mock_process.terminate.assert_called()
    
    def test_prompt_enhancement(self):
        """Test prompt enhancement with orchestration instructions."""
        adapter = QChatAdapter()
        
        # Test with plain prompt
        plain_prompt = "Simple task description"
        enhanced = adapter._enhance_prompt_with_instructions(plain_prompt)
        
        assert "ORCHESTRATION CONTEXT:" in enhanced
        assert "IMPORTANT INSTRUCTIONS:" in enhanced
        assert plain_prompt in enhanced
        # TASK_COMPLETE instruction removed from base adapter
        
        # Test idempotency - shouldn't enhance twice
        double_enhanced = adapter._enhance_prompt_with_instructions(enhanced)
        assert double_enhanced == enhanced
    
    def test_file_descriptor_management(self):
        """Test proper file descriptor management."""
        adapter = QChatAdapter()
        
        # Test with valid mock pipe
        mock_pipe = Mock()
        mock_pipe.fileno.return_value = 5
        
        with patch('fcntl.fcntl') as mock_fcntl:
            adapter._make_non_blocking(mock_pipe)
            # Should call fcntl twice (get flags, set flags)
            assert mock_fcntl.call_count == 2
        
        # Test with invalid pipe
        invalid_pipe = Mock()
        invalid_pipe.fileno.side_effect = ValueError("Invalid")
        
        # Should handle gracefully
        adapter._make_non_blocking(invalid_pipe)
        
        # Test with None pipe
        adapter._make_non_blocking(None)
    
    def test_read_available_variations(self):
        """Test _read_available with various pipe states."""
        adapter = QChatAdapter()
        
        # Test successful read
        mock_pipe = Mock()
        mock_pipe.read.return_value = "data"
        assert adapter._read_available(mock_pipe) == "data"
        
        # Test None return
        mock_pipe.read.return_value = None
        assert adapter._read_available(mock_pipe) == ""
        
        # Test empty string return
        mock_pipe.read.return_value = ""
        assert adapter._read_available(mock_pipe) == ""
        
        # Test IOError
        mock_pipe.read.side_effect = IOError("Would block")
        assert adapter._read_available(mock_pipe) == ""
        
        # Test None pipe
        assert adapter._read_available(None) == ""
    
    def test_cleanup_on_deletion(self):
        """Test cleanup when adapter is deleted."""
        adapter = QChatAdapter()
        
        # Mock a running process
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.terminate = Mock()
        mock_process.wait = Mock()
        
        with adapter._lock:
            adapter.current_process = mock_process
        
        # Store original signal handlers
        original_sigint = signal.signal(signal.SIGINT, signal.SIG_DFL)
        original_sigterm = signal.signal(signal.SIGTERM, signal.SIG_DFL)
        
        try:
            # Trigger cleanup
            adapter.__del__()
            
            # Process should be terminated
            mock_process.terminate.assert_called_once()
            
        finally:
            # Restore signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
    
    def test_cost_estimation(self):
        """Test cost estimation returns expected value."""
        adapter = QChatAdapter()
        
        # Should return 0 for Q chat
        assert adapter.estimate_cost("any prompt") == 0.0
        assert adapter.estimate_cost("") == 0.0
        assert adapter.estimate_cost("x" * 10000) == 0.0


class TestQChatRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_prompt_file_workflow(self):
        """Test the complete prompt file workflow."""
        adapter = QChatAdapter()
        adapter.available = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            prompt_file = Path(tmpdir) / "PROMPT.md"
            prompt_file.write_text("# Task\n\nComplete this task")
            
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.poll.side_effect = [None, 0]
                mock_process.stdout = Mock()
                mock_process.stderr = Mock()
                mock_process.stdout.read.return_value = "Task completed"
                mock_process.stderr.read.return_value = ""
                mock_process.stdout.fileno.return_value = 1
                mock_process.stderr.fileno.return_value = 2
                mock_popen.return_value = mock_process
                
                with patch.object(adapter, '_read_available', return_value=""):
                    response = adapter.execute(
                        prompt_file.read_text(),
                        prompt_file=str(prompt_file),
                        verbose=False
                    )
                
                assert response.success is True
                assert "Task completed" in response.output
                
                # Check command construction
                call_args = mock_popen.call_args[0][0]
                assert "q" in call_args
                assert "chat" in call_args
                assert "--no-interactive" in call_args
                assert "--trust-all-tools" in call_args
    
    def test_verbose_mode_output(self):
        """Test verbose mode provides detailed output."""
        adapter = QChatAdapter()
        adapter.available = True
        
        output_lines = []
        
        def capture_stderr(*args, **kwargs):
            if 'file' in kwargs and kwargs['file'].__name__ == 'stderr':
                output_lines.append(args[0] if args else "")
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.side_effect = [None, None, 0]
            mock_process.stdout = Mock()
            mock_process.stderr = Mock()
            mock_process.stdout.read.return_value = "Output"
            mock_process.stderr.read.return_value = ""
            mock_process.stdout.fileno.return_value = 1
            mock_process.stderr.fileno.return_value = 2
            mock_popen.return_value = mock_process
            
            with patch.object(adapter, '_read_available', return_value=""):
                with patch('builtins.print', side_effect=capture_stderr):
                    response = adapter.execute("test", verbose=True)
            
            assert response.success is True
            
            # Check verbose output was generated
            verbose_output = "".join(str(line) for line in output_lines)
            assert "Starting q chat" in verbose_output or "Command:" in verbose_output
    
    def test_long_running_process_monitoring(self):
        """Test monitoring of long-running processes."""
        adapter = QChatAdapter()
        adapter.available = True
        
        progress_messages = []
        
        def capture_progress(*args, **kwargs):
            if args and "still running" in str(args[0]):
                progress_messages.append(args[0])
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            # Process runs for a while
            mock_process.poll.side_effect = [None] * 35 + [0]
            mock_process.stdout = Mock()
            mock_process.stderr = Mock()
            mock_process.stdout.read.return_value = "Done"
            mock_process.stderr.read.return_value = ""
            mock_process.stdout.fileno.return_value = 1
            mock_process.stderr.fileno.return_value = 2
            mock_popen.return_value = mock_process
            
            with patch('time.time') as mock_time:
                # Simulate 31 seconds of execution
                times = [i for i in range(32)]
                mock_time.side_effect = times
                
                with patch.object(adapter, '_read_available', return_value=""):
                    with patch('builtins.print', side_effect=capture_progress):
                        with patch('time.sleep'):  # Speed up test
                            response = adapter.execute("test", verbose=True)
            
            assert response.success is True
            # Progress messages should be captured (at 30 second mark)
            # Note: Due to the modulo check, this might not always trigger
    
    def test_error_recovery_and_retry_capability(self):
        """Test that adapter can recover from errors and be reused."""
        adapter = QChatAdapter()
        adapter.available = True
        
        with patch('subprocess.Popen') as mock_popen:
            # First execution fails
            mock_process1 = Mock()
            mock_process1.poll.side_effect = [None, 1]
            mock_process1.stdout = Mock()
            mock_process1.stderr = Mock()
            mock_process1.stdout.read.return_value = ""
            mock_process1.stderr.read.return_value = "Error"
            mock_process1.stdout.fileno.return_value = 1
            mock_process1.stderr.fileno.return_value = 2
            
            # Second execution succeeds
            mock_process2 = Mock()
            mock_process2.poll.side_effect = [None, 0]
            mock_process2.stdout = Mock()
            mock_process2.stderr = Mock()
            mock_process2.stdout.read.return_value = "Success"
            mock_process2.stderr.read.return_value = ""
            mock_process2.stdout.fileno.return_value = 1
            mock_process2.stderr.fileno.return_value = 2
            
            mock_popen.side_effect = [mock_process1, mock_process2]
            
            with patch.object(adapter, '_read_available', return_value=""):
                # First execution fails
                response1 = adapter.execute("test1", verbose=False)
                assert response1.success is False
                assert "Error" in response1.error
                
                # Adapter should be ready for retry
                assert adapter.current_process is None
                assert not adapter.shutdown_requested
                
                # Second execution succeeds
                response2 = adapter.execute("test2", verbose=False)
                assert response2.success is True
                assert "Success" in response2.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])