# Ralph Orchestrator Implementation Plan

## Status: Initial Implementation Complete ✅

## Overview
Building an improved Ralph Wiggum orchestrator that maintains simplicity while adding key enhancements based on research.

## Architecture

### Core Components
1. **Orchestrator Engine** (`src/orchestrator.py`) ✅
   - Main loop implementation
   - Tool switching logic (claude, q chat, gemini fallback)
   - State management
   - Error recovery

2. **Tool Adapters** (`src/adapters/`) ✅
   - Claude CLI adapter
   - Q chat adapter  
   - Gemini adapter (fallback)
   - Unified interface for all tools

3. **Cost Tracking** (`src/metrics.py`) ✅
   - Token counting
   - Cost estimation
   - Usage limits

4. **Safety Module** (`src/safety.py`) ✅
   - Iteration limits
   - Safety checks
   - Circuit breaker

5. **Context Manager** (`src/context.py`) ✅
   - Prompt optimization
   - Context summarization
   - Stable prefix caching

## Implementation Phases

### Phase 1: Core Orchestrator (Completed)
- [x] Create main orchestrator class
- [x] Implement basic loop with claude
- [x] Add git-based checkpointing
- [x] Implement error recovery

### Phase 2: Multi-Tool Support (Completed)
- [x] Create tool adapter interface
- [x] Implement claude adapter
- [x] Implement q chat adapter
- [x] Add fallback chain logic

### Phase 3: Enhancements (Completed)
- [x] Add token tracking
- [x] Implement cost estimation
- [x] Add safety checks
- [x] Context optimization

### Phase 4: Testing (In Progress)
- [x] Unit tests for each component
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