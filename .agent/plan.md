# Ralph Orchestrator Implementation Plan

## Overview
Building an improved Ralph Wiggum orchestrator that maintains simplicity while adding key enhancements based on research.

## Architecture

### Core Components
1. **Orchestrator Engine** (`src/orchestrator.py`)
   - Main loop implementation
   - Tool switching logic (claude, q chat, gemini fallback)
   - State management
   - Error recovery

2. **Tool Adapters** (`src/adapters/`)
   - Claude CLI adapter
   - Q chat adapter  
   - Gemini adapter (fallback)
   - Unified interface for all tools

3. **Cost Tracking** (`src/metrics.py`)
   - Token counting
   - Cost estimation
   - Usage limits

4. **Safety Module** (`src/safety.py`)
   - Iteration limits
   - Safety checks
   - Circuit breaker

5. **Context Manager** (`src/context.py`)
   - Prompt optimization
   - Context summarization
   - Stable prefix caching

## Implementation Phases

### Phase 1: Core Orchestrator (Today)
- [ ] Create main orchestrator class
- [ ] Implement basic loop with claude
- [ ] Add git-based checkpointing
- [ ] Implement error recovery

### Phase 2: Multi-Tool Support (Today)
- [ ] Create tool adapter interface
- [ ] Implement claude adapter
- [ ] Implement q chat adapter
- [ ] Add fallback chain logic

### Phase 3: Enhancements (Today)
- [ ] Add token tracking
- [ ] Implement cost estimation
- [ ] Add safety checks
- [ ] Context optimization

### Phase 4: Testing (Today)
- [ ] Unit tests for each component
- [ ] Integration test with q chat
- [ ] Integration test with claude
- [ ] End-to-end test

## Key Design Principles
1. **Simplicity First**: Keep core loop under 400 lines
2. **Delegate Intelligence**: Let AI handle complex decisions
3. **Deterministic Failures**: Predictable errors are easier to fix
4. **Environmental Validation**: Use compilation/tests as guardrails

## Tool Integration Strategy

### Primary: Claude
```bash
claude -p "@PROMPT.md" --dangerously-skip-permissions
```

### Secondary: Q Chat
```bash
q chat "$(cat PROMPT.md)"
```

### Fallback: Gemini
```bash
gemini -p "@PROMPT.md"
```

## Success Metrics
- Latency: < 2s per iteration
- Error rate: < 0.5%
- Cost reduction: 30% via optimization
- Code simplicity: < 400 lines core

## Testing Strategy
1. Test with simple prompts first
2. Verify tool switching works
3. Test error recovery
4. Validate cost tracking
5. Full integration test with real task