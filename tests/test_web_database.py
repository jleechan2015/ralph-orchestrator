# ABOUTME: Test suite for the database module  
# ABOUTME: Verifies SQLite operations, data persistence, and statistics generation

import pytest
import os
import tempfile
import shutil
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sqlite3
import threading
import time

from src.ralph_orchestrator.web.database import DatabaseManager


class TestDatabaseManager:
    """Test suite for DatabaseManager functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test database."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def db_manager(self, temp_dir):
        """Create a DatabaseManager instance for testing."""
        db_path = os.path.join(temp_dir, 'test.db')
        manager = DatabaseManager(db_path)
        yield manager
        manager.close()
    
    def test_initialization(self, temp_dir):
        """Test database initialization and table creation."""
        db_path = os.path.join(temp_dir, 'test.db')
        manager = DatabaseManager(db_path)
        
        # Check database file exists
        assert os.path.exists(db_path)
        
        # Check tables exist
        with manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            
            assert 'orchestrator_runs' in tables
            assert 'iteration_history' in tables
            assert 'task_history' in tables
        
        manager.close()
    
    def test_create_run(self, db_manager):
        """Test creating an orchestrator run."""
        run_id = db_manager.create_run(
            orchestrator_id='test-orch-123',
            prompt_file='/path/to/prompt.md',
            metadata={'key': 'value'}
        )
        
        assert run_id is not None
        
        # Verify run was created
        with db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM orchestrator_runs WHERE id = ?",
                (run_id,)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[1] == 'test-orch-123'  # orchestrator_id
            assert row[2] == '/path/to/prompt.md'  # prompt_file
            assert json.loads(row[3]) == {'key': 'value'}  # metadata
            assert row[4] == 'running'  # status
    
    def test_update_run_status(self, db_manager):
        """Test updating run status."""
        run_id = db_manager.create_run('test-orch', '/prompt.md')
        
        # Test various status updates
        for status in ['paused', 'resumed', 'completed', 'failed']:
            success = db_manager.update_run_status(run_id, status)
            assert success
            
            with db_manager._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT status FROM orchestrator_runs WHERE id = ?",
                    (run_id,)
                )
                assert cursor.fetchone()[0] == status
        
        # Test invalid run_id
        assert not db_manager.update_run_status(99999, 'completed')
    
    def test_add_iteration(self, db_manager):
        """Test adding iteration history."""
        run_id = db_manager.create_run('test-orch', '/prompt.md')
        
        iteration_id = db_manager.add_iteration(
            run_id=run_id,
            iteration_number=1,
            agent_output='Test output',
            error='Test error',
            metrics={'time': 1.5}
        )
        
        assert iteration_id is not None
        
        # Verify iteration was added
        with db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM iteration_history WHERE id = ?",
                (iteration_id,)
            )
            row = cursor.fetchone()
            assert row[1] == run_id
            assert row[2] == 1  # iteration_number
            assert row[3] == 'Test output'
            assert row[4] == 'Test error'
            assert json.loads(row[5]) == {'time': 1.5}
    
    def test_add_task(self, db_manager):
        """Test adding task history."""
        run_id = db_manager.create_run('test-orch', '/prompt.md')
        
        task_id = db_manager.add_task(
            run_id=run_id,
            task_description='Test task',
            status='pending'
        )
        
        assert task_id is not None
        
        # Verify task was added
        with db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM task_history WHERE id = ?",
                (task_id,)
            )
            row = cursor.fetchone()
            assert row[1] == run_id
            assert row[2] == 'Test task'
            assert row[3] == 'pending'
    
    def test_update_task_status(self, db_manager):
        """Test updating task status."""
        run_id = db_manager.create_run('test-orch', '/prompt.md')
        task_id = db_manager.add_task(run_id, 'Test task', 'pending')
        
        # Update to in_progress
        success = db_manager.update_task_status(task_id, 'in_progress')
        assert success
        
        # Update to completed
        success = db_manager.update_task_status(task_id, 'completed')
        assert success
        
        # Verify timestamps
        with db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status, started_at, completed_at FROM task_history WHERE id = ?",
                (task_id,)
            )
            row = cursor.fetchone()
            assert row[0] == 'completed'
            assert row[1] is not None  # started_at
            assert row[2] is not None  # completed_at
    
    def test_get_recent_runs(self, db_manager):
        """Test retrieving recent runs."""
        # Create multiple runs
        run_ids = []
        for i in range(5):
            run_id = db_manager.create_run(f'orch-{i}', f'/prompt{i}.md')
            run_ids.append(run_id)
            time.sleep(0.01)  # Ensure different timestamps
        
        # Get recent runs
        runs = db_manager.get_recent_runs(limit=3)
        assert len(runs) == 3
        
        # Should be in reverse chronological order
        for i, run in enumerate(runs):
            assert run['orchestrator_id'] == f'orch-{4-i}'
    
    def test_get_run_details(self, db_manager):
        """Test retrieving detailed run information."""
        run_id = db_manager.create_run('test-orch', '/prompt.md')
        
        # Add iterations
        for i in range(3):
            db_manager.add_iteration(run_id, i+1, f'Output {i}')
        
        # Add tasks
        task_ids = []
        for i in range(2):
            task_id = db_manager.add_task(run_id, f'Task {i}', 'pending')
            task_ids.append(task_id)
        
        # Get run details
        details = db_manager.get_run_details(run_id)
        assert details is not None
        assert details['orchestrator_id'] == 'test-orch'
        assert len(details['iterations']) == 3
        assert len(details['tasks']) == 2
        
        # Test non-existent run
        assert db_manager.get_run_details(99999) is None
    
    def test_get_statistics(self, db_manager):
        """Test statistics generation."""
        # Create runs with different statuses
        run1 = db_manager.create_run('orch1', '/p1.md')
        run2 = db_manager.create_run('orch2', '/p2.md')
        run3 = db_manager.create_run('orch3', '/p3.md')
        
        db_manager.update_run_status(run1, 'completed')
        db_manager.update_run_status(run2, 'completed')
        db_manager.update_run_status(run3, 'failed')
        
        # Add iterations
        for run_id in [run1, run2]:
            for i in range(3):
                db_manager.add_iteration(run_id, i+1, 'output')
        
        stats = db_manager.get_statistics()
        assert stats['total_runs'] == 3
        assert stats['completed_runs'] == 2
        assert stats['failed_runs'] == 1
        assert stats['success_rate'] == pytest.approx(66.67, rel=0.01)
        assert stats['average_iterations'] == 2.0  # 6 iterations / 3 runs
    
    def test_cleanup_old_records(self, db_manager):
        """Test cleanup of old records."""
        # Create old run (simulated)
        with db_manager._get_connection() as conn:
            cursor = conn.cursor()
            old_date = (datetime.now() - timedelta(days=40)).isoformat()
            cursor.execute(
                """INSERT INTO orchestrator_runs 
                   (orchestrator_id, prompt_file, status, created_at)
                   VALUES (?, ?, ?, ?)""",
                ('old-orch', '/old.md', 'completed', old_date)
            )
            old_run_id = cursor.lastrowid
            conn.commit()
        
        # Create recent run
        recent_run = db_manager.create_run('recent-orch', '/recent.md')
        
        # Cleanup old records (older than 30 days)
        deleted = db_manager.cleanup_old_records(days=30)
        assert deleted == 1
        
        # Verify old run is gone, recent run remains
        with db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM orchestrator_runs")
            assert cursor.fetchone()[0] == 1
            
            cursor.execute(
                "SELECT orchestrator_id FROM orchestrator_runs WHERE id = ?",
                (recent_run,)
            )
            assert cursor.fetchone()[0] == 'recent-orch'
    
    def test_concurrent_access(self, db_manager):
        """Test thread-safe database operations."""
        results = {'errors': []}
        
        def worker(worker_id):
            try:
                for i in range(5):
                    run_id = db_manager.create_run(f'worker-{worker_id}', '/prompt.md')
                    db_manager.add_iteration(run_id, i, f'Output from {worker_id}')
                    db_manager.update_run_status(run_id, 'completed')
            except Exception as e:
                results['errors'].append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check no errors occurred
        assert len(results['errors']) == 0
        
        # Verify all data was written
        with db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM orchestrator_runs")
            assert cursor.fetchone()[0] == 50  # 10 workers * 5 runs each
    
    def test_json_metadata_handling(self, db_manager):
        """Test JSON serialization of metadata."""
        complex_metadata = {
            'nested': {'key': 'value'},
            'list': [1, 2, 3],
            'bool': True,
            'null': None
        }
        
        run_id = db_manager.create_run(
            'test-orch',
            '/prompt.md',
            metadata=complex_metadata
        )
        
        # Retrieve and verify
        details = db_manager.get_run_details(run_id)
        assert details['metadata'] == complex_metadata
    
    def test_error_handling(self, db_manager):
        """Test error handling in database operations."""
        # Test with invalid run_id
        assert not db_manager.update_run_status(99999, 'completed')
        assert not db_manager.update_task_status(99999, 'completed')
        
        # Test adding iteration to non-existent run
        result = db_manager.add_iteration(99999, 1, 'output')
        # Should handle gracefully (might return None or raise)
        
        # Test invalid status values (if validation exists)
        run_id = db_manager.create_run('test', '/prompt.md')
        # These should be handled gracefully
        db_manager.update_run_status(run_id, 'invalid_status')
    
    def test_database_persistence(self, temp_dir):
        """Test that data persists across manager instances."""
        db_path = os.path.join(temp_dir, 'persist.db')
        
        # Create data with first manager
        manager1 = DatabaseManager(db_path)
        run_id = manager1.create_run('test-orch', '/prompt.md')
        manager1.add_iteration(run_id, 1, 'Test output')
        manager1.close()
        
        # Read data with second manager
        manager2 = DatabaseManager(db_path)
        details = manager2.get_run_details(run_id)
        assert details is not None
        assert details['orchestrator_id'] == 'test-orch'
        assert len(details['iterations']) == 1
        manager2.close()
    
    def test_get_active_runs(self, db_manager):
        """Test retrieving active (running/paused) runs."""
        # Create runs with different statuses
        running = db_manager.create_run('running-orch', '/p1.md')
        paused = db_manager.create_run('paused-orch', '/p2.md')
        completed = db_manager.create_run('completed-orch', '/p3.md')
        
        db_manager.update_run_status(paused, 'paused')
        db_manager.update_run_status(completed, 'completed')
        
        # Get active runs
        with db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT orchestrator_id FROM orchestrator_runs 
                   WHERE status IN ('running', 'paused')
                   ORDER BY created_at DESC"""
            )
            active = [row[0] for row in cursor.fetchall()]
        
        assert 'running-orch' in active
        assert 'paused-orch' in active
        assert 'completed-orch' not in active