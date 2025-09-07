# Agent Scratchpad Directory

This directory serves as a workspace for the AI agent during Ralph orchestration.

## Directory Structure

- `prompts/` - Archived prompt files from each iteration
- `checkpoints/` - Git checkpoint references and state snapshots  
- `metrics/` - Performance metrics and execution statistics
- `plans/` - Long-term plans and todo lists
- `memory/` - Agent memory and context storage

## Usage

The orchestrator automatically manages this directory. Files here help with:

1. **Recovery** - Resume from checkpoints after failures
2. **Analysis** - Review iteration history and patterns
3. **Learning** - Improve prompts based on past errors
4. **Planning** - Store multi-step execution plans

## Important Notes

- This directory is managed by the orchestrator
- Files here are ephemeral and may be cleaned up
- Important data should be committed to the main repository
- Use `plans/` for persistent planning documents
