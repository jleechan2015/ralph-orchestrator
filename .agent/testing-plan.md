# Ralph Orchestrator Testing Plan
Date: 2025-09-07
Status: In Progress

## Overview
Testing the ralph-orchestrator implementation to verify it works with both `q chat` and `claude` as specified in requirements.

## Current Implementation Status
Based on git history and code review:
- ✅ Core orchestrator loop implemented
- ✅ Adapters for claude, qchat, and gemini
- ✅ Safety mechanisms (circuit breaker, checkpoints)
- ✅ Cost tracking and metrics
- ✅ CLI interface with comprehensive options
- ✅ Integration tests written and passed

## Testing Plan

### 1. Basic Functionality Tests
- [ ] Test simple math problem with q chat
- [ ] Test simple math problem with claude  
- [ ] Test task completion detection
- [ ] Test checkpoint creation

### 2. Loop Tests
- [ ] Test continuous iteration with PROMPT.md
- [ ] Test graceful shutdown (Ctrl+C)
- [ ] Test max iteration limits
- [ ] Test runtime limits

### 3. Recovery Tests
- [ ] Test error recovery with backoff
- [ ] Test checkpoint rollback
- [ ] Test prompt archiving

### 4. Feature Tests
- [ ] Test cost tracking
- [ ] Test verbose output
- [ ] Test dry-run mode
- [ ] Test custom prompt files

## Test Commands

### Q Chat Test
```bash
# Create test prompt
echo "What is 5 + 7? Write the answer and mark TASK_COMPLETE" > test_q.md

# Run with q chat
uv run python -m src.ralph_orchestrator --prompt test_q.md --tool qchat --max-iterations 2
```

### Claude Test  
```bash
# Create test prompt
echo "What is 8 + 9? Write the answer and mark TASK_COMPLETE" > test_claude.md

# Run with claude
uv run python -m src.ralph_orchestrator --prompt test_claude.md --tool claude --max-iterations 2
```

### Loop Test
```bash
# Create iterative task
cat > PROMPT.md << 'EOF'
# Task: Create a Python function

Create a function called `add_numbers` that:
1. Takes two parameters
2. Returns their sum
3. Has a docstring

When complete, add: <!-- TASK_COMPLETE -->
EOF

# Run orchestrator
uv run python -m src.ralph_orchestrator --max-iterations 5 --verbose
```

## Next Steps
1. Run each test command
2. Document results
3. Fix any issues found
4. Create demonstration video/screenshots
5. Push final version