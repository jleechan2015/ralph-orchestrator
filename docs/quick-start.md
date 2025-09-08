# Quick Start Guide

Get Ralph Orchestrator up and running in 5 minutes!

## Prerequisites

Before you begin, ensure you have:

- Python 3.8 or higher
- Git (for checkpointing features)
- At least one AI CLI tool installed

## Step 1: Install an AI Agent

Ralph works with multiple AI agents. Install at least one:

=== "Claude (Recommended)"

    ```bash
    npm install -g @anthropic-ai/claude-code
    # Or visit https://claude.ai/code for setup instructions
    ```

=== "Q Chat"

    ```bash
    pip install q-cli
    # Or follow instructions at https://github.com/qchat/qchat
    ```

=== "Gemini"

    ```bash
    npm install -g @google/gemini-cli
    # Configure with your API key
    ```

## Step 2: Clone Ralph Orchestrator

```bash
# Clone the repository
git clone https://github.com/mikeyobrien/ralph-orchestrator.git
cd ralph-orchestrator

# Install optional dependencies for monitoring
pip install psutil  # Recommended for system metrics
```

## Step 3: Create Your First Task

Create a `PROMPT.md` file with your task:

```markdown
# Task: Create a Todo List CLI

Build a Python command-line todo list application with:
- Add tasks
- List tasks
- Mark tasks as complete
- Save tasks to a JSON file

Include proper error handling and a help command.

The orchestrator will continue iterations until all requirements are met or limits reached.
```

## Step 4: Run Ralph

```bash
# Basic execution (auto-detects available agent)
python ralph_orchestrator.py --prompt PROMPT.md

# Or specify an agent explicitly
python ralph_orchestrator.py --agent claude --prompt PROMPT.md
```

## Step 5: Monitor Progress

Ralph will now:
1. Read your prompt file
2. Execute the AI agent
3. Check for completion
4. Iterate until done or limits reached

You'll see output like:
```
2025-09-08 10:30:45 - INFO - Starting Ralph Orchestrator v1.0.0
2025-09-08 10:30:45 - INFO - Using agent: claude
2025-09-08 10:30:45 - INFO - Starting iteration 1/100
2025-09-08 10:30:52 - INFO - Iteration 1 complete
2025-09-08 10:30:52 - INFO - Task not complete, continuing...
```

## What Happens Next?

Ralph will continue iterating until one of these conditions is met:

- 🎯 All requirements appear to be satisfied
- ⏱️ Maximum iterations reached (default: 100)
- ⏰ Maximum runtime exceeded (default: 4 hours)
- 💰 Token or cost limits reached
- ❌ Unrecoverable error occurs

## Basic Configuration

Control Ralph's behavior with command-line options:

```bash
# Limit iterations
python ralph_orchestrator.py --prompt PROMPT.md --max-iterations 50

# Set cost limit
python ralph_orchestrator.py --prompt PROMPT.md --max-cost 10.0

# Enable verbose logging
python ralph_orchestrator.py --prompt PROMPT.md --verbose

# Dry run (test without executing)
python ralph_orchestrator.py --prompt PROMPT.md --dry-run
```

## Example Tasks

### Simple Function

```markdown
Write a Python function that validates email addresses using regex.
Include comprehensive unit tests.
```

### Web Scraper

```markdown
Create a web scraper that:
1. Fetches the HackerNews homepage
2. Extracts the top 10 stories
3. Saves them to a JSON file
Use requests and BeautifulSoup.
```

### CLI Tool

```markdown
Build a markdown to HTML converter CLI tool:
- Accept input/output file arguments
- Support basic markdown syntax
- Add --watch mode for auto-conversion
```

## Next Steps

Now that you've run your first Ralph task:

- 📖 Read the [User Guide](guide/overview.md) for detailed configuration
- 🔒 Learn about [Security Features](advanced/security.md)
- 💰 Understand [Cost Management](guide/cost-management.md)
- 📊 Set up [Monitoring](advanced/monitoring.md)
- 🚀 Deploy to [Production](advanced/production-deployment.md)

## Troubleshooting

### Agent Not Found

If Ralph can't find an AI agent:
```bash
ERROR: No AI agents detected. Please install claude, q, or gemini.
```

**Solution**: Install one of the supported agents (see Step 1)

### Permission Denied

If you get permission errors:
```bash
chmod +x ralph_orchestrator.py
```

### Task Not Completing

If your task runs indefinitely:
- Check that your prompt includes clear completion criteria
- Ensure the agent can modify files and work towards completion
- Review iteration logs in `.agent/metrics/`

## Getting Help

- Check the [FAQ](faq.md)
- Read the [Troubleshooting Guide](troubleshooting.md)
- Open an [issue on GitHub](https://github.com/mikeyobrien/ralph-orchestrator/issues)
- Join the [discussions](https://github.com/mikeyobrien/ralph-orchestrator/discussions)

---

🎉 **Congratulations!** You've successfully run your first Ralph orchestration!