# Ralph Orchestrator

[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://mikeyobrien.github.io/ralph-orchestrator/)
[![Version](https://img.shields.io/badge/version-1.0.0-green)](https://github.com/mikeyobrien/ralph-orchestrator/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)

A production-ready implementation of the Ralph Wiggum software engineering technique - putting AI agents in a loop until the task is done.

> "Me fail English? That's unpossible!" - Ralph Wiggum

## 📚 Documentation

**[View Full Documentation](https://mikeyobrien.github.io/ralph-orchestrator/)** | [Quick Start](https://mikeyobrien.github.io/ralph-orchestrator/quick-start/) | [API Reference](https://mikeyobrien.github.io/ralph-orchestrator/api/) | [Examples](https://mikeyobrien.github.io/ralph-orchestrator/examples/)

## Overview

Ralph Orchestrator implements a simple but effective pattern for autonomous task completion using AI agents. It continuously runs an AI agent against a prompt file until the task is marked as complete or limits are reached.

Based on the Ralph Wiggum technique by [Geoffrey Huntley](https://ghuntley.com/ralph/), this implementation provides a robust, tested, and feature-complete orchestration system for AI-driven development.

## ✅ Production Ready - v1.0.0

- **Claude Integration**: ✅ COMPLETE
- **Q Chat Integration**: ✅ COMPLETE  
- **Gemini Integration**: ✅ COMPLETE
- **Core Orchestration**: ✅ OPERATIONAL
- **Test Suite**: ✅ 17 tests passing
- **Documentation**: ✅ [COMPLETE](https://mikeyobrien.github.io/ralph-orchestrator/)
- **Production Deployment**: ✅ [READY](https://mikeyobrien.github.io/ralph-orchestrator/advanced/production-deployment/)

## Features

- 🤖 **Multiple AI Agent Support**: Works with Claude, Q Chat, and Gemini CLI tools
- 🔍 **Auto-detection**: Automatically detects which AI agents are available
- 💾 **Checkpointing**: Git-based checkpointing for recovery and history
- 📚 **Prompt Archiving**: Tracks prompt evolution over iterations
- 🔄 **Error Recovery**: Automatic retry with exponential backoff
- 📊 **State Persistence**: Saves metrics and state for analysis
- ⏱️ **Configurable Limits**: Set max iterations and runtime limits
- 🧪 **Comprehensive Testing**: Full test coverage with unit and integration tests

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ralph-orchestrator.git
cd ralph-orchestrator

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

## Prerequisites

At least one AI CLI tool must be installed:

- **[Claude SDK](https://pypi.org/project/claude-code-sdk/)**
  ```bash
  # Automatically installed via dependencies
  # Requires ANTHROPIC_API_KEY environment variable with proper permissions:
  # - Read/Write access to conversations
  # - Model access (Claude 3.5 Sonnet or similar)
  # - Sufficient rate limits for continuous operation
  
  export ANTHROPIC_API_KEY="sk-ant-..."
  ```

- **[Q Chat](https://github.com/qchat/qchat)**
  ```bash
  # Follow installation instructions in repo
  ```

- **[Gemini CLI](https://github.com/google-gemini/gemini-cli)**
  ```bash
  npm install -g @google/gemini-cli
  ```

## Quick Start

### 1. Initialize a project
```bash
ralph init
```

This creates:
- `PROMPT.md` - Task description template
- `ralph.yml` - Configuration file
- `.agent/` - Workspace directories for prompts, checkpoints, metrics, plans, and memory

### 2. Configure Ralph (optional)
Edit `ralph.yml` to customize settings:
```yaml
# Core orchestrator settings
agent: auto                    # Which agent to use: claude, q, gemini, auto
prompt_file: PROMPT.md         # Path to prompt file
max_iterations: 100            # Maximum iterations before stopping
max_runtime: 14400             # Maximum runtime in seconds (4 hours)
checkpoint_interval: 5         # Git checkpoint every N iterations
retry_delay: 2                 # Delay between retries in seconds

# Resource limits
max_tokens: 1000000           # Maximum total tokens (1M)
max_cost: 50.0                # Maximum cost in USD
context_window: 200000        # Context window size in tokens
context_threshold: 0.8        # Trigger summarization at 80% of context

# Features
archive_prompts: true         # Archive prompt history
git_checkpoint: true          # Enable git checkpointing
enable_metrics: true          # Enable metrics collection
verbose: false                # Enable verbose output
dry_run: false                # Test mode without execution

# Adapter-specific configurations
adapters:
  claude:
    enabled: true
    timeout: 300              # Timeout in seconds
    max_retries: 3            # Max retry attempts
    args: []                  # Additional CLI arguments
    env:                      # Environment variables
      ANTHROPIC_API_KEY: ""   # Set your API key here or in environment
  
  q:
    enabled: true
    timeout: 300
    max_retries: 3
    args: []
    env: {}
  
  gemini:
    enabled: true
    timeout: 300
    max_retries: 3
    args: []
    env: {}
```

### 3. Edit PROMPT.md with your task
```markdown
# Task: Build a Python Calculator

Create a calculator module with:
- Basic operations (add, subtract, multiply, divide)
- Error handling for division by zero
- Unit tests for all functions

<!-- Ralph will add TASK_COMPLETE when done -->
```

### 4. Run Ralph
```bash
ralph run
# or with config file
ralph -c ralph.yml
```

## Usage

### Basic Commands

```bash
# Run with auto-detected agent
ralph

# Use configuration file
ralph -c ralph.yml

# Use specific agent
ralph run -a claude
ralph run -a q
ralph run -a gemini

# Check status
ralph status

# Clean workspace
ralph clean

# Dry run (test without executing)
ralph run --dry-run
```

### Advanced Options

```bash
ralph [OPTIONS]

Options:
  -c, --config CONFIG             Configuration file (YAML format)
  --agent {claude,q,gemini,auto}  AI agent to use (default: auto)
  --prompt PROMPT                  Prompt file path (default: PROMPT.md)
  --max-iterations N               Maximum iterations (default: 100)
  --max-runtime SECONDS           Maximum runtime (default: 14400)
  --checkpoint-interval N          Checkpoint every N iterations (default: 5)
  --retry-delay SECONDS           Delay between retries (default: 2)
  --no-git                        Disable git checkpointing
  --no-archive                    Disable prompt archiving
  --verbose                       Enable verbose output
  --dry-run                       Test mode without executing agents
```

## How It Works

### The Ralph Loop

```
┌─────────────────┐
│  Read PROMPT.md │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Execute AI Agent│<──────┐
└────────┬────────┘       │
         │                │
         v                │
┌─────────────────┐       │
│ Check Complete? │───No──┘
└────────┬────────┘
         │Yes
         v
┌─────────────────┐
│      Done!      │
└─────────────────┘
```

### Execution Flow

1. **Initialization**: Creates `.agent/` directories and validates prompt file
2. **Agent Detection**: Auto-detects available AI agents (claude, q, gemini)
3. **Iteration Loop**: 
   - Executes AI agent with current prompt
   - Monitors for task completion marker
   - Creates checkpoints at intervals
   - Handles errors with retry logic
4. **Completion**: Stops when:
   - Task marked complete (TASK_COMPLETE found)
   - Max iterations reached
   - Max runtime exceeded
   - Too many consecutive errors

## Project Structure

```
ralph-orchestrator/
├── src/
│   └── ralph_orchestrator/
│       ├── __main__.py      # CLI entry point
│       ├── main.py          # Main orchestrator loop
│       ├── orchestrator.py  # Core orchestration logic
│       ├── adapters/        # AI agent adapters
│       │   ├── base.py      # Base adapter interface
│       │   ├── claude.py    # Claude SDK adapter
│       │   ├── gemini.py    # Gemini CLI adapter
│       │   └── qchat.py     # Q Chat adapter
│       ├── context.py       # Context management
│       ├── metrics.py       # Metrics tracking
│       └── safety.py        # Safety checks
├── tests/                   # Test suite
│   ├── test_orchestrator.py
│   ├── test_adapters.py
│   └── test_integration.py
├── docs/                    # Documentation
├── PROMPT.md               # Task description (user created)
├── pyproject.toml          # Project configuration
├── .agent/                 # CLI workspace (created by init)
│   ├── prompts/            # Prompt workspace
│   ├── checkpoints/        # Checkpoint markers
│   ├── metrics/            # Metrics data
│   ├── plans/              # Planning documents
│   └── memory/             # Agent memory
├── .ralph/                 # Runtime metrics directory
└── prompts/                # Prompt archive directory
    └── archive/            # Archived prompt history
```

## Testing

### Run Test Suite

```bash
# All tests
uv run pytest -v

# With coverage
uv run pytest --cov=ralph_orchestrator

# Specific test file
uv run pytest tests/test_orchestrator.py -v

# Integration tests only
uv run pytest tests/test_integration.py -v
```

### Test Coverage

- ✅ Unit tests for all core functions
- ✅ Integration tests with mocked agents
- ✅ CLI interface tests
- ✅ Error handling and recovery tests
- ✅ State persistence tests

## Examples

### Simple Function

```bash
echo "Write a Python function to check if a number is prime" > PROMPT.md
ralph run -a claude --max-iterations 5
```

### Web Application

```bash
cat > PROMPT.md << 'EOF'
Build a Flask web app with:
- User registration and login
- SQLite database
- Basic CRUD operations
- Bootstrap UI
EOF

ralph run --max-iterations 50
```

### Test-Driven Development

```bash
cat > PROMPT.md << 'EOF'
Implement a linked list in Python using TDD:
1. Write tests first
2. Implement methods to pass tests
3. Add insert, delete, search operations
4. Ensure 100% test coverage
EOF

ralph run -a q --verbose
```

## Monitoring

### Check Status
```bash
# One-time status check
ralph status

# Example output:
Ralph Orchestrator Status
=========================
Prompt: PROMPT.md exists
Status: IN PROGRESS
Latest metrics: .ralph/metrics_20250907_154435.json
{
  "iteration_count": 15,
  "runtime": 234.5,
  "errors": 0
}
```

### View Logs
```bash
# If using verbose mode
ralph run --verbose 2>&1 | tee ralph.log

# Check git history
git log --oneline | grep "Ralph checkpoint"
```

## Error Recovery

Ralph handles errors gracefully:

- **Retry Logic**: Failed iterations retry after configurable delay
- **Error Limits**: Stops after 5 consecutive errors
- **Timeout Protection**: 5-minute timeout per iteration
- **State Persistence**: Can analyze failures from saved state
- **Git Recovery**: Can reset to last working checkpoint

### Manual Recovery

```bash
# Check last error
cat .ralph/metrics_*.json | jq '.errors[-1]'

# Reset to last checkpoint
git reset --hard HEAD

# Clean and restart
ralph clean
ralph run
```

## Best Practices

1. **Clear Task Definition**: Write specific, measurable requirements
2. **Incremental Goals**: Break complex tasks into smaller steps
3. **Success Markers**: Define clear completion criteria
4. **Regular Checkpoints**: Use default 5-iteration checkpoints
5. **Monitor Progress**: Use `ralph status` to track iterations
6. **Version Control**: Commit PROMPT.md before starting

## Troubleshooting

### Agent Not Found
```bash
# For Claude, ensure API key is set with proper permissions
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify Claude API key permissions:
# - Should have access to Claude 3.5 Sonnet or similar model
# - Need sufficient rate limits (at least 40,000 tokens/minute)
# - Requires read/write access to the API

# For Q and Gemini, check CLI tools are installed
which q
which gemini

# Install missing CLI tools as needed
```

### Task Not Completing
```bash
# Check if TASK_COMPLETE marker is being added
grep TASK_COMPLETE PROMPT.md

# Review agent errors
cat .agent/metrics/state_*.json | jq '.errors'

# Try different agent
ralph run -a gemini
```

### Performance Issues
```bash
# Reduce iteration timeout
ralph run --max-runtime 1800

# Increase checkpoint frequency
ralph run --checkpoint-interval 3
```

## Research & Theory

The Ralph Wiggum technique is based on several key principles:

1. **Simplicity Over Complexity**: Keep orchestration minimal (~400 lines)
2. **Deterministic Failure**: Fail predictably in an unpredictable world
3. **Context Recovery**: Use git and state files for persistence
4. **Human-in-the-Loop**: Allow manual intervention when needed

For detailed research and theoretical foundations, see the [research directory](../README.md).

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`uv run pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- **[Geoffrey Huntley](https://ghuntley.com/ralph/)** - Creator of the Ralph Wiggum technique
- **[Harper Reed](https://harper.blog/)** - Spec-driven development methodology
- **Anthropic, Google, Q** - For providing excellent AI CLI tools

## Support

- **Documentation**: [Full Documentation](https://mikeyobrien.github.io/ralph-orchestrator/)
- **Deployment Guide**: [Production Deployment](https://mikeyobrien.github.io/ralph-orchestrator/advanced/production-deployment/)
- **Issues**: [GitHub Issues](https://github.com/mikeyobrien/ralph-orchestrator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mikeyobrien/ralph-orchestrator/discussions)
- **Research**: [Ralph Wiggum Research](../)

## Version History

- **v1.0.0** (2025-09-07)
  - Initial release with Claude, Q, and Gemini support
  - Comprehensive test suite (17 tests)
  - Production-ready error handling
  - Full documentation
  - Git-based checkpointing
  - State persistence and metrics

---

*"I'm learnding!" - Ralph Wiggum*