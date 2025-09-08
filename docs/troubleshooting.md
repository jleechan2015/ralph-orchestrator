# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Agent Not Found
**Problem**: `ralph: command 'claude' not found`

**Solutions**:
1. Verify agent installation:
   ```bash
   which claude
   which gemini
   which q
   ```

2. Install missing agent:
   ```bash
   # Claude
   npm install -g @anthropic-ai/claude-code
   
   # Gemini
   npm install -g @google/gemini-cli
   ```

3. Add to PATH:
   ```bash
   export PATH=$PATH:/usr/local/bin
   ```

#### Permission Denied
**Problem**: `Permission denied: './ralph'`

**Solution**:
```bash
chmod +x ralph ralph_orchestrator.py
```

### Execution Issues

#### Task Running Too Long
**Problem**: Ralph runs maximum iterations without achieving goals

**Possible Causes**:
1. Unclear or overly complex task description
2. Agent not making progress towards objectives
3. Task scope too large for iteration limits

**Solutions**:
1. Check iteration progress and logs:
   ```bash
   ralph status
   ```

2. Break down complex tasks:
   ```markdown
   # Instead of:
   Build a complete web application
   
   # Try:
   Create a Flask app with one endpoint that returns "Hello World"
   ```

3. Increase iteration limits or try different agent:
   ```bash
   ralph run --max-iterations 200
   ralph run --agent gemini
   ```

#### Agent Timeout
**Problem**: `Agent execution timed out`

**Solutions**:
1. Increase timeout:
   ```python
   # In ralph.json
   {
     "timeout_per_iteration": 600
   }
   ```

2. Reduce prompt complexity:
   - Break large tasks into smaller ones
   - Remove unnecessary context

3. Check system resources:
   ```bash
   htop
   free -h
   ```

#### Repeated Errors
**Problem**: Same error occurs in multiple iterations

**Solutions**:
1. Check error pattern:
   ```bash
   cat .agent/metrics/state_*.json | jq '.errors'
   ```

2. Clear workspace and retry:
   ```bash
   ralph clean
   ralph run
   ```

3. Manual intervention:
   - Fix the specific issue
   - Add clarification to PROMPT.md
   - Resume execution

### Git Issues

#### Checkpoint Failed
**Problem**: `Failed to create checkpoint`

**Solutions**:
1. Initialize Git repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. Check Git status:
   ```bash
   git status
   ```

3. Fix Git configuration:
   ```bash
   git config user.email "you@example.com"
   git config user.name "Your Name"
   ```

#### Uncommitted Changes Warning
**Problem**: `Uncommitted changes detected`

**Solutions**:
1. Commit changes:
   ```bash
   git add .
   git commit -m "Save work"
   ```

2. Stash changes:
   ```bash
   git stash
   ralph run
   git stash pop
   ```

3. Disable Git operations:
   ```bash
   ralph run --no-git
   ```

### Context Issues

#### Context Window Exceeded
**Problem**: `Context window limit exceeded`

**Symptoms**:
- Agent forgets earlier instructions
- Incomplete responses
- Errors about missing information

**Solutions**:
1. Reduce file sizes:
   ```bash
   # Split large files
   split -l 500 large_file.py part_
   ```

2. Use more concise prompt:
   ```markdown
   # Remove unnecessary details
   # Focus on current task
   ```

3. Switch to higher-context agent:
   ```bash
   # Claude has 200K context
   ralph run --agent claude
   ```

4. Clear iteration history:
   ```bash
   rm .agent/prompts/prompt_*.md
   ```

### Performance Issues

#### Slow Execution
**Problem**: Iterations taking too long

**Solutions**:
1. Check system resources:
   ```bash
   top
   df -h
   iostat
   ```

2. Reduce parallel operations:
   - Close other applications
   - Limit background processes

3. Use faster agent:
   ```bash
   # Q is typically faster
   ralph run --agent q
   ```

#### High Memory Usage
**Problem**: Ralph consuming excessive memory

**Solutions**:
1. Set resource limits:
   ```python
   # In ralph.json
   {
     "resource_limits": {
       "memory_mb": 2048
     }
   }
   ```

2. Clean old state files:
   ```bash
   find .agent -name "*.json" -mtime +7 -delete
   ```

3. Restart Ralph:
   ```bash
   pkill -f ralph_orchestrator
   ralph run
   ```

### State and Metrics Issues

#### Corrupted State File
**Problem**: `Invalid state file`

**Solutions**:
1. Remove corrupted file:
   ```bash
   rm .agent/metrics/state_latest.json
   ```

2. Restore from backup:
   ```bash
   cp .agent/metrics/state_*.json .agent/metrics/state_latest.json
   ```

3. Reset state:
   ```bash
   ralph clean
   ```

#### Missing Metrics
**Problem**: No metrics being collected

**Solutions**:
1. Check metrics directory:
   ```bash
   ls -la .agent/metrics/
   ```

2. Create directory if missing:
   ```bash
   mkdir -p .agent/metrics
   ```

3. Check permissions:
   ```bash
   chmod 755 .agent/metrics
   ```

## Error Messages

### Common Error Codes

| Error | Meaning | Solution |
|-------|---------|----------|
| `Exit code 1` | General failure | Check logs for details |
| `Exit code 130` | Interrupted (Ctrl+C) | Normal interruption |
| `Exit code 137` | Killed (out of memory) | Increase memory limits |
| `Exit code 124` | Timeout | Increase timeout value |

### Agent-Specific Errors

#### Claude Errors
```
"Rate limit exceeded"
```
**Solution**: Add delay between iterations or upgrade API plan

```
"Invalid API key"
```
**Solution**: Check Claude CLI configuration

#### Gemini Errors
```
"Quota exceeded"
```
**Solution**: Wait for quota reset or upgrade plan

```
"Model not available"
```
**Solution**: Check Gemini CLI version and update

#### Q Chat Errors
```
"Connection refused"
```
**Solution**: Ensure Q service is running

## Debug Mode

### Enable Verbose Logging

```bash
# Maximum verbosity
ralph run --verbose

# With debug environment
DEBUG=1 ralph run

# Save logs
ralph run --verbose 2>&1 | tee debug.log
```

### Inspect Execution

```python
# Add debug points in PROMPT.md
print("DEBUG: Reached checkpoint 1")
```

### Trace Execution

```bash
# Trace system calls
strace -o trace.log ralph run

# Profile Python execution
python -m cProfile ralph_orchestrator.py
```

## Recovery Procedures

### From Failed State

1. **Save current state**:
   ```bash
   cp -r .agent .agent.backup
   ```

2. **Analyze failure**:
   ```bash
   tail -n 100 .agent/logs/ralph.log
   ```

3. **Fix issue**:
   - Update PROMPT.md
   - Fix code errors
   - Clear problematic files

4. **Resume or restart**:
   ```bash
   # Resume from checkpoint
   ralph run
   
   # Or start fresh
   ralph clean && ralph run
   ```

### From Git Checkpoint

```bash
# List checkpoints
git log --oneline | grep checkpoint

# Reset to checkpoint
git reset --hard <commit-hash>

# Resume execution
ralph run
```

## Getting Help

### Self-Diagnosis

Run the diagnostic script:
```bash
cat > diagnose.sh << 'EOF'
#!/bin/bash
echo "Ralph Orchestrator Diagnostic"
echo "============================"
echo "Agents available:"
which claude && echo "  ✓ Claude" || echo "  ✗ Claude"
which gemini && echo "  ✓ Gemini" || echo "  ✗ Gemini"
which q && echo "  ✓ Q" || echo "  ✗ Q"
echo ""
echo "Git status:"
git status --short
echo ""
echo "Ralph status:"
./ralph status
echo ""
echo "Recent errors:"
grep ERROR .agent/logs/*.log 2>/dev/null | tail -5
EOF
chmod +x diagnose.sh
./diagnose.sh
```

### Community Support

1. **GitHub Issues**: [Report bugs](https://github.com/mikeyobrien/ralph-orchestrator/issues)
2. **Discussions**: [Ask questions](https://github.com/mikeyobrien/ralph-orchestrator/discussions)
3. **Discord**: Join the community chat

### Reporting Bugs

Include in bug reports:
1. Ralph version: `ralph --version`
2. Agent versions
3. Error messages
4. PROMPT.md content
5. Diagnostic output
6. Steps to reproduce

## Prevention Tips

### Best Practices

1. **Start simple**: Test with basic tasks first
2. **Regular checkpoints**: Use default 5-iteration interval
3. **Monitor progress**: Check status frequently
4. **Version control**: Commit before running Ralph
5. **Resource limits**: Set appropriate limits
6. **Clear requirements**: Write specific, testable criteria

### Pre-flight Checklist

Before running Ralph:
- [ ] PROMPT.md is clear and specific
- [ ] Git repository is clean
- [ ] Agents are installed and working
- [ ] Sufficient disk space available
- [ ] No sensitive data in prompt
- [ ] Backup important files