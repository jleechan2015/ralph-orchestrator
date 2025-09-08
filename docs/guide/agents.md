# AI Agents Guide

Ralph Orchestrator supports multiple AI agents, each with unique capabilities and cost structures. This guide helps you choose and configure the right agent for your task.

## Supported Agents

### Claude (Anthropic)

Claude is Anthropic's advanced AI assistant, known for nuanced understanding and high-quality outputs.

**Strengths:**
- Excellent code generation and debugging
- Strong reasoning and analysis
- Comprehensive documentation writing
- Ethical and safe responses
- Large context window (200K tokens)

**Best For:**
- Complex software development
- Technical documentation
- Research and analysis
- Creative writing
- Problem-solving requiring deep reasoning

**Installation:**
```bash
npm install -g @anthropic-ai/claude-cli
```

**Usage:**
```bash
python ralph_orchestrator.py --agent claude
```

**Cost:**
- Input: $3.00 per million tokens
- Output: $15.00 per million tokens

### Q Chat

Q Chat is a cost-effective AI assistant suitable for many general tasks, now with production-ready adapter implementation.

**Strengths:**
- Good general-purpose capabilities
- Fast response times with streaming support
- Cost-effective for simple tasks
- Reliable for straightforward operations
- Thread-safe concurrent message processing
- Robust error handling and recovery
- Graceful shutdown and resource cleanup

**Best For:**
- Simple coding tasks
- Basic documentation
- Data processing
- Quick prototypes
- Budget-conscious operations
- High-concurrency workloads
- Long-running batch processes

**Installation:**
```bash
pip install q-cli
```

**Usage:**
```bash
python ralph_orchestrator.py --agent q

# Short form
python ralph_orchestrator.py -a q
```

**Production Features:**
- **Message Queue**: Thread-safe async message processing
- **Error Recovery**: Automatic retry with exponential backoff
- **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM
- **Resource Management**: Proper cleanup of processes and threads
- **Timeout Handling**: Configurable timeouts with partial output preservation
- **Non-blocking I/O**: Prevents deadlocks in pipe communication
- **Concurrent Processing**: Handles multiple requests simultaneously

**Cost:**
- Input: $0.50 per million tokens (estimated)
- Output: $1.50 per million tokens (estimated)

### Gemini (Google)

Google's Gemini offers strong capabilities with multimodal understanding.

**Strengths:**
- Excellent at data analysis
- Strong mathematical capabilities
- Good code understanding
- Multimodal capabilities (Pro version)
- Competitive pricing

**Best For:**
- Data science tasks
- Mathematical computations
- Code analysis
- Research tasks
- Multi-language support

**Installation:**
```bash
pip install google-generativeai
```

**Usage:**
```bash
python ralph_orchestrator.py --agent gemini
```

**Cost:**
- Input: $0.50 per million tokens
- Output: $1.50 per million tokens

## Auto-Detection

Ralph Orchestrator can automatically detect and use available agents:

```bash
python ralph_orchestrator.py --agent auto
```

**Detection Order:**
1. Claude (if installed)
2. Q Chat (if installed)
3. Gemini (if installed)

## Agent Comparison

| Feature | Claude | Q Chat | Gemini |
|---------|--------|--------|---------|
| **Context Window** | 200K | 100K | 128K |
| **Code Quality** | Excellent | Good | Very Good |
| **Documentation** | Excellent | Good | Good |
| **Speed** | Moderate | Fast | Fast |
| **Cost** | High | Low | Low |
| **Reasoning** | Excellent | Good | Very Good |
| **Creativity** | Excellent | Good | Good |
| **Math/Data** | Very Good | Good | Excellent |

## Choosing the Right Agent

### Decision Tree

```mermaid
graph TD
    A[Select Agent] --> B{Task Type?}
    B -->|Complex Code| C[Claude]
    B -->|Simple Task| D{Budget?}
    B -->|Data Analysis| E[Gemini]
    D -->|Limited| F[Q Chat]
    D -->|Flexible| G[Claude/Gemini]
    B -->|Documentation| H{Quality Need?}
    H -->|High| I[Claude]
    H -->|Standard| J[Q Chat/Gemini]
```

### Task-Agent Mapping

| Task Type | Recommended Agent | Alternative |
|-----------|------------------|-------------|
| **Web API Development** | Claude | Gemini |
| **CLI Tool Creation** | Claude | Q Chat |
| **Data Processing** | Gemini | Claude |
| **Documentation** | Claude | Gemini |
| **Testing** | Claude | Q Chat |
| **Refactoring** | Claude | Gemini |
| **Simple Scripts** | Q Chat | Gemini |
| **Research** | Claude | Gemini |
| **Prototyping** | Q Chat | Gemini |
| **Production Code** | Claude | - |

## Agent Configuration

### Claude Configuration

```bash
# Standard Claude usage
python ralph_orchestrator.py --agent claude

# With specific model
python ralph_orchestrator.py \
  --agent claude \
  --agent-args "--model claude-3-sonnet-20240229"

# With custom parameters
python ralph_orchestrator.py \
  --agent claude \
  --agent-args "--temperature 0.7 --max-tokens 4096"
```

### Q Chat Configuration

```bash
# Standard Q usage
python ralph_orchestrator.py --agent q

# With custom parameters
python ralph_orchestrator.py \
  --agent q \
  --agent-args "--context-length 50000"

# Production configuration with enhanced settings
python ralph_orchestrator.py \
  --agent q \
  --max-iterations 100 \
  --retry-delay 2 \
  --checkpoint-interval 10 \
  --verbose

# High-concurrency configuration
python ralph_orchestrator.py \
  --agent q \
  --agent-args "--async --timeout 300" \
  --max-iterations 200
```

**Environment Variables:**
```bash
# Set Q chat timeout (default: 120 seconds)
export QCHAT_TIMEOUT=300

# Enable verbose logging
export QCHAT_VERBOSE=1

# Configure retry attempts
export QCHAT_MAX_RETRIES=5
```

### Gemini Configuration

```bash
# Standard Gemini usage
python ralph_orchestrator.py --agent gemini

# With specific model
python ralph_orchestrator.py \
  --agent gemini \
  --agent-args "--model gemini-pro"
```

## Agent-Specific Features

### Claude Features

- **Constitutional AI**: Built-in safety and ethics
- **Code Understanding**: Deep comprehension of complex codebases
- **Long Context**: Handles up to 200K tokens
- **Nuanced Responses**: Understands subtle requirements

```bash
# Leverage Claude's long context
python ralph_orchestrator.py \
  --agent claude \
  --context-window 200000 \
  --context-threshold 0.9
```

### Q Chat Features

- **Speed**: Fast response times with streaming support
- **Efficiency**: Lower resource usage with optimized memory management
- **Simplicity**: Straightforward for basic tasks
- **Concurrency**: Thread-safe operations for parallel processing
- **Reliability**: Automatic error recovery and retry mechanisms
- **Production-Ready**: Signal handling, graceful shutdown, resource cleanup

**Production Capabilities:**
```bash
# Quick iterations with Q
python ralph_orchestrator.py \
  --agent q \
  --max-iterations 100 \
  --retry-delay 1

# Async execution with timeout
python ralph_orchestrator.py \
  --agent q \
  --agent-args "--async --timeout 300" \
  --checkpoint-interval 10

# Stress testing configuration
python ralph_orchestrator.py \
  --agent q \
  --max-iterations 500 \
  --metrics-interval 10 \
  --verbose

# Long-running batch processing
python ralph_orchestrator.py \
  --agent q \
  --checkpoint-interval 5 \
  --max-cost 50.0 \
  --retry-delay 5
```

**Monitoring and Logging:**
- Thread-safe logging for concurrent operations
- Detailed error messages with stack traces
- Performance metrics collection
- Resource usage tracking
- Message queue status monitoring

### Gemini Features

- **Data Excellence**: Superior at data tasks
- **Mathematical Prowess**: Strong calculation abilities
- **Multi-language**: Good support for various programming languages

```bash
# Data processing with Gemini
python ralph_orchestrator.py \
  --agent gemini \
  --prompt data_analysis.md
```

## Multi-Agent Strategies

### Sequential Processing

Process with different agents for different phases:

```bash
# Phase 1: Research with Claude
python ralph_orchestrator.py --agent claude --prompt research.md

# Phase 2: Implementation with Q
python ralph_orchestrator.py --agent q --prompt implement.md

# Phase 3: Documentation with Claude
python ralph_orchestrator.py --agent claude --prompt document.md
```

### Cost Optimization

Start with cheaper agents, escalate if needed:

```bash
# Try Q first
python ralph_orchestrator.py --agent q --max-cost 2.0

# If unsuccessful, try Claude
python ralph_orchestrator.py --agent claude --max-cost 20.0
```

## Agent Performance Tuning

### Claude Optimization

```bash
# Optimized for quality
python ralph_orchestrator.py \
  --agent claude \
  --max-iterations 50 \
  --checkpoint-interval 5 \
  --context-window 200000

# Optimized for speed
python ralph_orchestrator.py \
  --agent claude \
  --max-iterations 20 \
  --retry-delay 1
```

### Q Chat Optimization

```bash
# Maximum efficiency
python ralph_orchestrator.py \
  --agent q \
  --max-iterations 200 \
  --checkpoint-interval 20 \
  --metrics-interval 50
```

### Gemini Optimization

```bash
# Data-heavy tasks
python ralph_orchestrator.py \
  --agent gemini \
  --context-window 128000 \
  --max-tokens 500000
```

## Troubleshooting Agents

### Common Issues

1. **Agent Not Found**
   ```bash
   # Check installation
   which claude  # or q, gemini
   
   # Use auto-detection
   python ralph_orchestrator.py --agent auto --dry-run
   ```

2. **Rate Limiting**
   ```bash
   # Increase retry delay
   python ralph_orchestrator.py --retry-delay 10
   ```

3. **Context Overflow**
   ```bash
   # Adjust context settings
   python ralph_orchestrator.py \
     --context-window 100000 \
     --context-threshold 0.7
   ```

4. **Poor Output Quality**
   ```bash
   # Switch to higher-quality agent
   python ralph_orchestrator.py --agent claude
   ```

### Agent Diagnostics

```bash
# Test agent availability
python ralph_orchestrator.py --agent auto --dry-run --verbose

# Check agent performance
python ralph_orchestrator.py \
  --agent claude \
  --max-iterations 1 \
  --verbose \
  --metrics-interval 1
```

## Cost Management by Agent

### Budget Allocation

```bash
# Low budget: Use Q
python ralph_orchestrator.py --agent q --max-cost 5.0

# Medium budget: Use Gemini
python ralph_orchestrator.py --agent gemini --max-cost 25.0

# High budget: Use Claude
python ralph_orchestrator.py --agent claude --max-cost 100.0
```

### Cost Tracking

Monitor costs per agent:

```bash
# Enable detailed metrics
python ralph_orchestrator.py \
  --agent claude \
  --metrics-interval 1 \
  --verbose
```

## Best Practices

### 1. Match Agent to Task

- **Complex logic**: Use Claude
- **Simple tasks**: Use Q Chat
- **Data work**: Use Gemini

### 2. Start Small

Test with few iterations first:

```bash
python ralph_orchestrator.py --agent auto --max-iterations 5
```

### 3. Monitor Performance

Track metrics for optimization:

```bash
python ralph_orchestrator.py --metrics-interval 5 --verbose
```

### 4. Use Auto-Detection

Let the system choose when unsure:

```bash
python ralph_orchestrator.py --agent auto
```

### 5. Consider Costs

Balance quality with budget:

- Development: Use Q Chat
- Testing: Use Gemini
- Production: Use Claude

## Next Steps

- Master [Prompt Engineering](prompts.md) for better results
- Learn about [Cost Management](cost-management.md)
- Understand [Checkpointing](checkpointing.md) strategies
- Explore [Configuration](configuration.md) options