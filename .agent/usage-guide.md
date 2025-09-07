# Ralph Orchestrator Usage Guide

## Quick Start

The Ralph Orchestrator implements the Ralph Wiggum technique for persistent AI agent execution. It works with both `q chat` and `claude` CLI tools.

### Basic Usage

```bash
# Run with Claude (default)
python run_ralph.py

# Run with Q Chat
python run_ralph.py --tool qchat

# Custom prompt file
python run_ralph.py --prompt MY_TASK.md
```

## Installation

### Prerequisites

1. **Python 3.8+** installed
2. At least one AI CLI tool:
   - **Claude CLI**: `pip install claude-cli` or follow Anthropic's installation
   - **Q Chat**: Install from your package manager or source
   - **Gemini** (optional): `pip install gemini-cli`

### Setup

```bash
# Clone the repository
cd ralph-orchestrator

# Install dependencies (using uv)
uv sync

# Or with pip
pip install -e .
```

## Creating Prompts

Create a `PROMPT.md` file with your task description:

```markdown
# Task: Build a Calculator

Create a Python calculator module with the following functions:
- add(a, b): Returns sum of a and b
- subtract(a, b): Returns difference
- multiply(a, b): Returns product
- divide(a, b): Returns quotient (handle division by zero)

Include unit tests for all functions.
```

The orchestrator will:
1. Read your prompt
2. Execute it with the chosen AI tool
3. Monitor for completion (looks for "TASK_COMPLETE" marker)
4. Handle errors and retry if needed
5. Save checkpoints periodically

## Command-Line Options

```bash
python run_ralph.py [OPTIONS]

Options:
  --prompt FILE           Path to prompt file (default: PROMPT.md)
  --tool TOOL            AI tool to use: claude, qchat, gemini (default: claude)
  --max-iterations N     Maximum iterations (default: 100)
  --max-runtime SECONDS  Maximum runtime in seconds (default: 14400)
  --track-costs          Enable cost tracking
  --max-cost DOLLARS     Maximum allowed cost (default: 10.00)
  --checkpoint-interval N Git checkpoint frequency (default: 5)
  --verbose              Enable debug output
  --dry-run              Show config without executing
```

## Examples

### Simple Task

```bash
echo "Write a hello world program in Python" > PROMPT.md
python run_ralph.py --max-iterations 1
```

### Complex Project

```bash
cat > PROJECT.md << EOF
Build a REST API with:
- FastAPI framework
- User authentication
- CRUD operations for a blog
- SQLite database
- Comprehensive tests
EOF

python run_ralph.py --prompt PROJECT.md --tool claude --max-iterations 50
```

### Cost-Limited Execution

```bash
python run_ralph.py --track-costs --max-cost 5.00
```

## How It Works

The orchestrator implements the Ralph Wiggum technique:

1. **Simple Loop**: Continuously reads prompt and executes with AI tool
2. **Persistence**: Keeps trying until task is complete or limits reached
3. **Safety**: Built-in circuit breakers and resource limits
4. **Recovery**: Automatic retry with exponential backoff
5. **State**: Git checkpoints for resuming interrupted work

## Monitoring Progress

### Logs
- Real-time output shows each iteration
- Detailed logs in `.ralph/` directory
- Metrics saved as JSON for analysis

### Checkpoints
- Git commits created every N iterations
- Allows resuming from last known good state
- Review with `git log --oneline`

### Metrics
```bash
# View latest metrics
cat .ralph/metrics_*.json | jq .
```

## Troubleshooting

### Tool Not Available
```bash
# Check if tool is installed
which claude
which q

# Verify adapter can find it
python -c "from ralph_orchestrator.adapters.claude import ClaudeAdapter; print(ClaudeAdapter().available)"
```

### Task Not Completing
- Ensure prompt is clear and specific
- Add explicit success criteria
- Check if tool needs more iterations
- Review logs for error patterns

### Performance Issues
- Reduce max iterations for testing
- Use checkpoint intervals to save progress
- Enable verbose mode to see details
- Consider switching tools if one is struggling

## Testing

```bash
# Run integration tests
python test_ralph_orchestrator.py

# Test specific tool
python -c "
from ralph_orchestrator.adapters.qchat import QChatAdapter
adapter = QChatAdapter()
print(f'Q Chat available: {adapter.available}')
"
```

## Advanced Usage

### Custom Adapters

Create new adapters by extending `ToolAdapter`:

```python
from ralph_orchestrator.adapters.base import ToolAdapter, ToolResponse

class MyToolAdapter(ToolAdapter):
    def check_availability(self) -> bool:
        # Check if tool is installed
        pass
    
    def execute(self, prompt: str, **kwargs) -> ToolResponse:
        # Execute tool with prompt
        pass
```

### Prompt Engineering

For best results:
- Be specific about file locations
- Include success criteria
- Break complex tasks into steps
- Provide examples when helpful
- Add "TASK_COMPLETE" marker requirement

### Integration with CI/CD

```yaml
# GitHub Actions example
- name: Run Ralph Orchestrator
  run: |
    echo "${{ inputs.prompt }}" > PROMPT.md
    python run_ralph.py --tool claude --max-iterations 10
```

## Philosophy

The Ralph Wiggum technique embraces:
- **Simplicity**: Basic loop that just works
- **Persistence**: "I'm helping!" attitude
- **Delegation**: Let AI handle complexity
- **Pragmatism**: Good enough > perfect

## Support

For issues or questions:
1. Check logs in `.ralph/` directory
2. Review this guide and examples
3. Consult the research documents in parent directory
4. Create an issue with logs and reproduction steps