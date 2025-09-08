# Ralph Orchestrator Production Deployment Guide
Version 1.0.0 | Generated: 2025-09-08

## Overview
This guide provides comprehensive instructions for deploying Ralph Orchestrator to production environments, including documentation hosting, CI/CD setup, and operational considerations.

## Table of Contents
1. [Documentation Deployment](#documentation-deployment)
2. [Application Deployment](#application-deployment)
3. [CI/CD Pipeline](#cicd-pipeline)
4. [Monitoring & Observability](#monitoring--observability)
5. [Security Considerations](#security-considerations)
6. [Maintenance & Operations](#maintenance--operations)

## Documentation Deployment

### Prerequisites
- Python 3.8+ with pip
- Git repository with push access
- GitHub Pages enabled (for GitHub hosting)

### Local Development
```bash
# Install MkDocs and dependencies
pip install mkdocs mkdocs-material pymdown-extensions

# Navigate to project root
cd ralph-orchestrator

# Serve documentation locally
mkdocs serve
# Documentation available at http://localhost:8000
```

### Building Static Site
```bash
# Build static documentation
mkdocs build

# Output will be in ./site directory
ls -la site/
```

### GitHub Pages Deployment

#### Method 1: Manual Deployment
```bash
# Build and deploy to GitHub Pages
mkdocs gh-deploy

# This will:
# 1. Build the documentation
# 2. Push to gh-pages branch
# 3. Configure GitHub Pages to serve from gh-pages branch
```

#### Method 2: GitHub Actions (Automated)
Create `.github/workflows/docs.yml`:
```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'mkdocs.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install mkdocs mkdocs-material
          
      - name: Build documentation
        run: mkdocs build
        
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2
        with:
          path: ./site

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v2
```

### Alternative Hosting Options

#### Netlify
```toml
# netlify.toml
[build]
  command = "pip install mkdocs mkdocs-material && mkdocs build"
  publish = "site"

[build.environment]
  PYTHON_VERSION = "3.11"
```

#### Vercel
```json
// vercel.json
{
  "buildCommand": "pip install mkdocs mkdocs-material && mkdocs build",
  "outputDirectory": "site",
  "installCommand": "pip install --user mkdocs mkdocs-material"
}
```

#### Docker
```dockerfile
# Dockerfile.docs
FROM python:3.11-slim

WORKDIR /docs

COPY requirements-docs.txt .
RUN pip install -r requirements-docs.txt

COPY . .
RUN mkdocs build

FROM nginx:alpine
COPY --from=0 /docs/site /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Application Deployment

### System Requirements
- Python 3.8+
- Git
- At least one AI CLI tool (Claude, Q, or Gemini)
- 2GB RAM minimum
- 10GB disk space

### Installation Methods

#### Method 1: Direct Installation
```bash
# Clone repository
git clone https://github.com/mikeyobrien/ralph-orchestrator.git
cd ralph-orchestrator

# Make executable
chmod +x ralph_orchestrator.py ralph

# Install Python dependencies (if any)
pip install -r requirements.txt

# Verify installation
./ralph --version
```

#### Method 2: Docker Container
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install AI CLI tools
RUN npm install -g @anthropic-ai/claude-code

# Copy application
WORKDIR /app
COPY . .

# Make scripts executable
RUN chmod +x ralph_orchestrator.py ralph

# Set entrypoint
ENTRYPOINT ["./ralph"]
```

Build and run:
```bash
docker build -t ralph-orchestrator .
docker run -it -v $(pwd):/workspace ralph-orchestrator run
```

#### Method 3: Kubernetes Deployment
```yaml
# ralph-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ralph-orchestrator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ralph-orchestrator
  template:
    metadata:
      labels:
        app: ralph-orchestrator
    spec:
      containers:
      - name: ralph
        image: ralph-orchestrator:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        volumeMounts:
        - name: workspace
          mountPath: /workspace
        env:
        - name: CLAUDE_API_KEY
          valueFrom:
            secretKeyRef:
              name: ralph-secrets
              key: claude-api-key
      volumes:
      - name: workspace
        persistentVolumeClaim:
          claimName: ralph-workspace-pvc
```

### Configuration

#### Environment Variables
```bash
# Required
export RALPH_AGENT=claude  # or q, gemini, auto

# Optional
export RALPH_MAX_ITERATIONS=100
export RALPH_MAX_RUNTIME=14400
export RALPH_CHECKPOINT_INTERVAL=5
export RALPH_LOG_LEVEL=INFO
export RALPH_METRICS_ENABLED=true
```

#### Configuration File
```yaml
# ralph-config.yaml
agent: claude
max_iterations: 100
max_runtime: 14400
checkpoint_interval: 5
archive_prompts: true
git_checkpoint: true
verbose: false
max_tokens: 1000000
max_cost: 50.0
context_window: 200000
enable_metrics: true
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/release.yml
name: Release Pipeline

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Run tests
        run: |
          pip install pytest
          pytest tests/
          
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: |
          docker build -t ralph-orchestrator:${GITHUB_REF#refs/tags/} .
          
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push ralph-orchestrator:${GITHUB_REF#refs/tags/}
          
  deploy-docs:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Deploy documentation
        run: |
          pip install mkdocs mkdocs-material
          mkdocs gh-deploy --force
```

## Monitoring & Observability

### Metrics Collection
```python
# Enable built-in metrics
config = RalphConfig(
    enable_metrics=True,
    metrics_interval=10
)
```

### Prometheus Integration
```yaml
# prometheus-config.yaml
scrape_configs:
  - job_name: 'ralph-orchestrator'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
```

### Logging Configuration
```python
# Structured logging setup
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'iteration': getattr(record, 'iteration', None),
            'agent': getattr(record, 'agent', None)
        }
        return json.dumps(log_obj)

# Apply formatter
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

### Alerting Rules
```yaml
# alerts.yaml
groups:
  - name: ralph-alerts
    rules:
      - alert: HighTokenUsage
        expr: ralph_tokens_total > 900000
        for: 5m
        annotations:
          summary: "High token usage detected"
          
      - alert: TaskStalled
        expr: rate(ralph_iterations_total[10m]) == 0
        for: 20m
        annotations:
          summary: "No progress in last 20 minutes"
          
      - alert: HighCost
        expr: ralph_cost_total > 40
        annotations:
          summary: "Approaching cost limit"
```

## Security Considerations

### API Key Management
```bash
# Use environment variables
export CLAUDE_API_KEY="sk-..."

# Or use secrets management
kubectl create secret generic ralph-secrets \
  --from-literal=claude-api-key=$CLAUDE_API_KEY
```

### File System Security
```python
# Enable path validation
config = RalphConfig(
    allow_unsafe_paths=False,  # Default
    max_prompt_size=10485760   # 10MB limit
)
```

### Network Security
```yaml
# Network policy for Kubernetes
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ralph-network-policy
spec:
  podSelector:
    matchLabels:
      app: ralph-orchestrator
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS only
```

## Maintenance & Operations

### Health Checks
```bash
# Add health check endpoint
./ralph health

# Check specific components
./ralph health --check agents
./ralph health --check git
```

### Backup & Recovery
```bash
# Backup workspace
tar -czf ralph-backup-$(date +%Y%m%d).tar.gz \
  .ralph/ \
  .agent/ \
  PROMPT.md

# Restore from backup
tar -xzf ralph-backup-20250908.tar.gz
```

### Performance Tuning
```python
# Optimize for large contexts
config = RalphConfig(
    context_window=200000,
    context_threshold=0.8,
    checkpoint_interval=3,  # More frequent checkpoints
    max_tokens=2000000     # Higher token limit for complex tasks
)
```

### Troubleshooting

#### Common Issues

1. **Agent not found**
   ```bash
   # Verify agent installation
   which claude
   which q
   which gemini
   ```

2. **Git checkpoint failures**
   ```bash
   # Initialize git if needed
   git init
   git config user.email "ralph@example.com"
   git config user.name "Ralph Orchestrator"
   ```

3. **High memory usage**
   ```bash
   # Limit context window
   ./ralph run --context-window 50000
   ```

4. **Token limit exceeded**
   ```bash
   # Enable summarization
   ./ralph run --context-threshold 0.5
   ```

### Monitoring Commands
```bash
# View metrics
./ralph metrics

# Show current status
./ralph status

# List checkpoints
./ralph checkpoints list

# View logs
tail -f .ralph/ralph-orchestrator.log
```

## Production Checklist

### Pre-Deployment
- [ ] Test suite passes
- [ ] Documentation complete
- [ ] Security scan completed
- [ ] Performance benchmarks meet requirements
- [ ] Backup strategy defined
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] Runbook created

### Deployment
- [ ] Deploy to staging first
- [ ] Run smoke tests
- [ ] Verify monitoring
- [ ] Check logs for errors
- [ ] Test rollback procedure
- [ ] Deploy to production
- [ ] Verify production deployment
- [ ] Update status page

### Post-Deployment
- [ ] Monitor metrics for 24 hours
- [ ] Review performance data
- [ ] Document any issues
- [ ] Update runbook if needed
- [ ] Schedule retrospective

## Support & Resources

### Documentation
- Main Site: https://mikeyobrien.github.io/ralph-orchestrator/
- API Reference: https://mikeyobrien.github.io/ralph-orchestrator/api/
- Examples: https://mikeyobrien.github.io/ralph-orchestrator/examples/

### Community
- GitHub Issues: https://github.com/mikeyobrien/ralph-orchestrator/issues
- Discussions: https://github.com/mikeyobrien/ralph-orchestrator/discussions

### Contact
- Email: support@ralph-orchestrator.io
- Twitter: @RalphOrchestrator

## Version History
- v1.0.0 - Initial production release
- v0.9.0 - Beta release with core features
- v0.5.0 - Alpha release for testing