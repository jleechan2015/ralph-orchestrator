"""Tests for YAML configuration loading."""

import pytest
import tempfile
import yaml
from pathlib import Path

from ralph_orchestrator.main import RalphConfig, AdapterConfig, AgentType


def test_yaml_config_loading():
    """Test loading configuration from YAML file."""
    config_data = {
        'agent': 'claude',
        'max_iterations': 50,
        'verbose': True,
        'adapters': {
            'claude': {
                'enabled': True,
                'timeout': 600,
                'args': ['--model', 'claude-3-sonnet']
            },
            'q': False
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        config = RalphConfig.from_yaml(config_path)
        
        assert config.agent == AgentType.CLAUDE
        assert config.max_iterations == 50
        assert config.verbose is True
        
        # Test adapter configs
        claude_config = config.get_adapter_config('claude')
        assert claude_config.enabled is True
        assert claude_config.timeout == 600
        assert claude_config.args == ['--model', 'claude-3-sonnet']
        
        q_config = config.get_adapter_config('q')
        assert q_config.enabled is False
        
    finally:
        Path(config_path).unlink()


def test_adapter_config_defaults():
    """Test adapter configuration defaults."""
    config = RalphConfig()
    adapter_config = config.get_adapter_config('nonexistent')
    
    assert adapter_config.enabled is True
    assert adapter_config.timeout == 300
    assert adapter_config.max_retries == 3
    assert adapter_config.args == []
    assert adapter_config.env == {}


def test_yaml_config_missing_file():
    """Test error handling for missing config file."""
    with pytest.raises(FileNotFoundError):
        RalphConfig.from_yaml('nonexistent.yml')
