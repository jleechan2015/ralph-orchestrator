# Ralph Orchestrator 🎯

A production-ready implementation of the Ralph Wiggum orchestration technique for AI agents. Put your AI in a loop until the task is done, with enterprise-grade safety, monitoring, and cost controls.

> "Me fail English? That's unpossible!" - Ralph Wiggum

## ✨ Features

### Core Capabilities
- 🤖 **Multi-agent support** (Claude, Q Chat, Gemini) with auto-detection
- 🔄 **Automatic iteration** until task completion
- 💾 **Git-based checkpointing** for state recovery
- 📦 **Prompt archiving** and history tracking

### Production Features (NEW)
- 💰 **Token & Cost Management**
  - Real-time token tracking and cost calculation
  - Configurable spending limits
  - Per-agent pricing models
  
- 📊 **Context Window Management**
  - Automatic overflow detection
  - Intelligent prompt summarization
  - Configurable window sizes
  
- 🔒 **Security Controls**
  - Input sanitization and validation
  - Command injection prevention
  - Path traversal protection
  - Dangerous pattern detection
  
- 📈 **Production Monitoring**
  - System metrics (CPU, memory, disk)
  - Performance tracking
  - Success/failure rates
  - Detailed JSON exports
  
- 🛡️ **Resilience & Recovery**
  - Graceful shutdown handling
  - Automatic retries with backoff
  - Circuit breaker for errors
  - State persistence

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/mikeyobrien/ralph-orchestrator.git
cd ralph-orchestrator

# Install Python package (if using pip)
pip install psutil  # Optional but recommended for metrics

# Install at least one AI agent
npm install -g @anthropic-ai/claude-cli  # Claude
pip install q-cli                        # Q Chat
pip install google-generativeai          # Gemini
```

## 📖 Usage

### Quick Start

```bash
# Auto-detect agent and run task
python ralph_orchestrator.py --prompt PROMPT.md

# Dry run to test configuration
python ralph_orchestrator.py --dry-run --prompt PROMPT.md
```

### Production Usage

```bash
# Full production configuration
python ralph_orchestrator.py \
  --agent claude \
  --prompt task.md \
  --max-iterations 100 \
  --max-runtime 14400 \
  --max-tokens 1000000 \
  --max-cost 50.0 \
  --context-window 200000 \
  --checkpoint-interval 5 \
  --metrics-interval 10
```

### Cost-Controlled Execution

```bash
# Set spending limits
python ralph_orchestrator.py \
  --prompt expensive_task.md \
  --max-tokens 500000 \
  --max-cost 25.0
```

### High-Security Mode

```bash
# Strict security validation
python ralph_orchestrator.py \
  --prompt secure_task.md \
  --max-prompt-size 1048576 \
  --no-git  # Disable git operations
```

## ⚙️ Command Line Options

### Core Options
- `--agent`: Choose AI agent (claude/q/gemini/auto)
- `--prompt`: Path to prompt file (default: PROMPT.md)
- `--max-iterations`: Maximum iterations (default: 100)
- `--max-runtime`: Maximum runtime in seconds (default: 14400)

### Cost & Token Management
- `--max-tokens`: Maximum total tokens (default: 1,000,000)
- `--max-cost`: Maximum cost in USD (default: $50.00)
- `--context-window`: Context window size (default: 200,000)
- `--context-threshold`: Summarization threshold (default: 0.8)

### Security Options
- `--max-prompt-size`: Max prompt file size in bytes (default: 10MB)
- `--allow-unsafe-paths`: Allow potentially unsafe paths

### Monitoring & Debugging
- `--metrics-interval`: Metrics logging interval (default: 10)
- `--no-metrics`: Disable metrics collection
- `--verbose`: Enable verbose logging
- `--dry-run`: Test without executing agents

### Checkpoint & Recovery
- `--checkpoint-interval`: Iterations between checkpoints (default: 5)
- `--retry-delay`: Delay between retries in seconds (default: 2)
- `--no-git`: Disable git checkpointing
- `--no-archive`: Disable prompt archiving

## 🔄 How It Works

1. **Initialization**
   - Validates prompt file security
   - Sets up monitoring and metrics
   - Creates working directories
   - Detects available AI agents

2. **Iteration Loop**
   - Checks token/cost limits before execution
   - Monitors context window usage
   - Executes AI agent with sanitized prompt
   - Tracks token usage and costs
   - Records performance metrics
   - Checks for TASK_COMPLETE marker

3. **Safety Controls**
   - Validates inputs for malicious patterns
   - Prevents command injection
   - Handles context overflow via summarization
   - Stops on limit breaches

4. **Checkpoint & Recovery**
   - Creates git checkpoints at intervals
   - Archives prompt versions
   - Saves state for recovery
   - Handles graceful shutdown

5. **Completion**
   - Saves final metrics and state
   - Reports usage statistics
   - Exports detailed logs

## 📝 Configuration

### Prompt File Format

Create a `PROMPT.md` file with your task:

```markdown
# Task Description

Your detailed task instructions here.

The agent should modify this file as it works.
When the task is complete, add "TASK_COMPLETE" to this file.
```

### Metrics & Monitoring

Metrics are saved to:
- `.agent/metrics/state_*.json` - Orchestrator state
- `.agent/metrics/metrics_*.json` - Performance data
- `.agent/prompts/` - Archived prompts
- `.agent/checkpoints/` - Git history

## 🧪 Testing

### Run Test Suite

```bash
# Run comprehensive test suite
python test_production_readiness.py

# Expected output: 18 tests, all passing
```

### Integration Testing

```bash
# Test Q Chat
echo "Write a hello world function" > test.md
python ralph_orchestrator.py --agent q --prompt test.md --max-iterations 2

# Test Claude
python ralph_orchestrator.py --agent claude --prompt test.md --max-iterations 2
```

## 📊 Production Metrics

- **Startup Time**: < 1 second
- **Iteration Overhead**: < 0.5 seconds  
- **Memory Usage**: < 50MB base
- **Test Coverage**: 18 tests, 100% passing
- **Production Readiness**: 92/100

## 🔒 Security

The orchestrator includes multiple security layers:
- Input validation and sanitization
- Command injection prevention
- Path traversal protection
- File size limits
- Dangerous pattern detection

For additional security, use `--allow-unsafe-paths` with caution.

## 📈 Cost Management

Built-in cost tracking for:
- **Claude 3.5 Sonnet**: $3/1M input, $15/1M output
- **Q Chat**: $0.50/1M input, $1.50/1M output (estimated)
- **Gemini Pro**: $0.50/1M input, $1.50/1M output

Set limits with `--max-cost` to prevent overspending.

## 🤝 Contributing

Contributions are welcome! Please:
1. Run the test suite
2. Follow existing code style
3. Add tests for new features
4. Update documentation

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Based on the Ralph Wiggum orchestration technique by [Geoffrey Huntley](https://ghuntley.com/ralph/). See research documents for theoretical foundations.

---

**Version**: 1.0.0-production  
**Status**: Production Ready  
**Last Updated**: 2025-09-07