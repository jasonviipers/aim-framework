# AIM Framework: Adaptive Intelligence Mesh

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://aim-framework.readthedocs.io/)

A distributed coordination system for AI deployment and interaction that revolutionizes how AI systems collaborate and scale.

## Overview

The AIM Framework creates a mesh network of AI agents that can:

- **Dynamic Capability Routing**: Route queries to specialized micro-agents based on context, urgency, and required expertise
- **Persistent Context Weaving**: Create "context threads" that persist across sessions and can be selectively shared between agents
- **Adaptive Resource Scaling**: Automatically spawn or hibernate agents based on demand patterns
- **Cross-Agent Learning Propagation**: Share knowledge gained by one agent across the mesh without centralized retraining
- **Confidence-Based Collaboration**: Enable agents to detect their uncertainty and automatically collaborate with other agents

The core innovation of AIM is the **Intent Graph** - a real-time graph of user intentions, project contexts, and capability needs that allows the system to anticipate requirements and pre-position resources.

## Key Features

### 🔀 Dynamic Capability Routing
Instead of having one large model handle everything, AIM routes queries to specialized micro-agents based on context, urgency, and required expertise. A coding question might route through a code-specialist agent, then to a security-review agent, then to a documentation agent.

### 🧵 Persistent Context Weaving
Each interaction creates "context threads" that persist across sessions and can be selectively shared between agents. Your conversation about a project continues seamlessly whether you're asking about code, design, or deployment.

### 📈 Adaptive Resource Scaling
The mesh automatically spawns or hibernates agents based on demand patterns. During high coding activity, more programming agents activate. During research phases, more analysis agents come online.

### 🧠 Cross-Agent Learning Propagation
When one agent learns something valuable (like a common error pattern), it propagates this knowledge through the mesh without centralized retraining.

### 🤝 Confidence-Based Collaboration
Agents can detect their uncertainty and automatically collaborate with other agents, creating dynamic expert panels for complex problems.

### 🎯 Intent Graph
Builds a real-time graph of user intentions, project contexts, and capability needs to anticipate requirements and pre-position resources.

## Installation

### From PyPI (Recommended)

```bash
pip install aim-framework
```

### From Source

```bash
git clone https://github.com/jasonviipers/aim-framework.git
cd aim-framework
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/jasonviipers/aim-framework.git
cd aim-framework
pip install -e ".[dev,docs,api,visualization]"
```

### Docker Installation

```bash
# Pull from Docker Hub
docker pull aim-framework:latest

# Or build locally
docker build -t aim-framework:latest .

# Run with Docker Compose
docker-compose up -d
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes cluster
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n aim-framework
```

## Quick Start

### 1. Basic Usage

```python
import asyncio
from aim import AIMFramework, Config

async def main():
    # Create and initialize framework
    framework = AIMFramework()
    await framework.initialize()
    
    # Create a request
    from aim import Request
    request = Request(
        user_id="user_123",
        content="Create a Python function to calculate prime numbers",
        task_type="code_generation"
    )
    
    # Process the request
    response = await framework.process_request(request)
    print(f"Response: {response.content}")
    
    # Shutdown
    await framework.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Using the CLI

Start the AIM server:

```bash
aim-server --host 0.0.0.0 --port 5000
```

Initialize a new project:

```bash
aim-init my-aim-project
cd my-aim-project
pip install -r requirements.txt
python main.py
```

Run benchmarks:

```bash
aim-benchmark --benchmark-type latency --num-requests 100
```

### 3. Creating Custom Agents

```python
from aim import Agent, AgentCapability, Request, Response

class CustomCodeAgent(Agent):
    def __init__(self):
        super().__init__(
            capabilities={AgentCapability.CODE_GENERATION},
            description="Custom code generation agent",
            version="1.0.0"
        )
    
    async def process_request(self, request: Request) -> Response:
        # Your custom logic here
        result = f"Generated code for: {request.content}"
        
        return Response(
            request_id=request.request_id,
            agent_id=self.agent_id,
            content=result,
            confidence=0.9,
            success=True
        )

# Register with framework
framework.register_agent(CustomCodeAgent())
```

### 4. Configuration

```python
from aim import Config

# Load from file
config = Config("config.json")

# Or create programmatically
config = Config({
    "framework": {
        "name": "My AIM Framework",
        "log_level": "INFO"
    },
    "api": {
        "host": "0.0.0.0",
        "port": 5000
    },
    "agents": {
        "max_agents_per_type": 5
    }
})

framework = AIMFramework(config)
```

## Architecture

The AIM Framework consists of five main layers:

1. **Interface Layer**: APIs and user interfaces
2. **Coordination Layer**: Dynamic routing, context weaving, and collaboration
3. **Agent Layer**: Specialized micro-agents for different capabilities
4. **Resource Management Layer**: Adaptive scaling and load balancing
5. **Knowledge Layer**: Learning propagation and Intent Graph

## API Reference

### Core Classes

- `AIMFramework`: Main orchestrator class
- `Agent`: Base class for creating custom agents
- `Request`/`Response`: Communication primitives
- `ContextThread`: Persistent context management
- `Config`: Configuration management

### Agent Capabilities

The framework supports various built-in capabilities:

- `CODE_GENERATION`: Generate code in various languages
- `SECURITY_REVIEW`: Security analysis and vulnerability detection
- `DOCUMENTATION`: Generate and maintain documentation
- `DATA_ANALYSIS`: Analyze and visualize data
- `DESIGN`: UI/UX design and prototyping
- `RESEARCH`: Information gathering and analysis
- `TESTING`: Test generation and execution
- `DEPLOYMENT`: Application deployment and DevOps

## Examples

### Multi-Agent Collaboration

```python
# Request that requires multiple agents
request = Request(
    user_id="user_123",
    content="Create a secure web API with documentation",
    task_type="code_generation"
)

# Framework automatically routes through:
# 1. Code generation agent
# 2. Security review agent  
# 3. Documentation agent

response = await framework.process_request(request)
```

### Context Persistence

```python
# Create a context thread
thread_id = await framework.create_context_thread(
    user_id="user_123",
    initial_context={"project": "web_api", "language": "python"}
)

# First request
request1 = Request(
    user_id="user_123",
    content="Create a Flask API",
    task_type="code_generation",
    context_thread_id=thread_id
)

# Second request (context is maintained)
request2 = Request(
    user_id="user_123", 
    content="Add authentication to the API",
    task_type="code_generation",
    context_thread_id=thread_id  # Same thread
)
```

### Performance Monitoring

```python
# Get performance metrics
metrics = await framework.get_performance_metrics()
print(f"Average latency: {metrics['avg_latency']}")
print(f"Throughput: {metrics['avg_throughput']}")

# Get framework status
status = framework.get_framework_status()
print(f"Active agents: {status['active_agents']}")
```

## Deployment

The AIM Framework supports multiple deployment strategies for different environments and scale requirements.

### Development Deployment

For local development and testing:

```bash
# Start the development server
aim-server --config config/development.json --debug

# Or use the Python API directly
python examples/basic_usage.py
```

### Production Deployment

#### Option 1: Docker (Recommended)

```bash
# Single container deployment
docker run -d \
  --name aim-framework \
  -p 5000:5000 \
  -v $(pwd)/config:/app/config \
  -v aim-logs:/app/logs \
  -v aim-data:/app/data \
  --restart unless-stopped \
  aim-framework:latest

# Multi-service deployment with Docker Compose
docker-compose -f docker-compose.yml up -d

# Scale the application
docker-compose up -d --scale aim-server=3
```

#### Option 2: Systemd Service

```bash
# Use the automated deployment script
python deploy.py --environment production --method systemd

# Manual service management
sudo systemctl start aim-framework
sudo systemctl enable aim-framework
sudo systemctl status aim-framework
```

#### Option 3: Kubernetes

```bash
# Deploy to Kubernetes cluster
kubectl apply -f k8s/

# Monitor deployment
kubectl get pods -n aim-framework -w

# Scale deployment
kubectl scale deployment aim-framework --replicas=5 -n aim-framework
```

#### Option 4: Cloud Platforms

**AWS ECS:**
```bash
# Deploy using AWS CLI
aws ecs create-service --cluster aim-cluster --service-name aim-framework --task-definition aim-framework:1
```

**Google Cloud Run:**
```bash
# Deploy to Cloud Run
gcloud run deploy aim-framework --image gcr.io/PROJECT-ID/aim-framework --platform managed
```

**Azure Container Instances:**
```bash
# Deploy to Azure
az container create --resource-group myResourceGroup --name aim-framework --image aim-framework:latest
```

### Load Balancing and High Availability

For production environments, configure load balancing with Nginx:

```nginx
upstream aim_backend {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://aim_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Monitoring and Observability

Monitor your deployment with built-in metrics:

```bash
# Health check
curl http://localhost:5000/health

# Performance metrics
curl http://localhost:5000/metrics

# Run performance tests
python -m aim.utils.performance_test --url http://localhost:5000
```

### Security Configuration

For production deployments, ensure proper security:

```json
{
  "security": {
    "api_key_required": true,
    "rate_limit": "100/minute",
    "cors_enabled": true,
    "allowed_origins": ["https://yourdomain.com"],
    "ssl_enabled": true,
    "jwt_secret": "your-secure-jwt-secret"
  }
}
```

### Backup and Recovery

Automated backup configuration:

```bash
# Create backup
python deploy.py --backup

# Restore from backup
tar -xzf backups/aim_backup_20240115_103000.tar.gz
```

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md) and [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md).

## Configuration

The framework supports extensive configuration through JSON files or environment variables:

```json
{
  "framework": {
    "name": "AIM Framework",
    "version": "1.0.0",
    "log_level": "INFO"
  },
  "agents": {
    "min_agents_per_type": 1,
    "max_agents_per_type": 5,
    "default_timeout": 30.0
  },
  "context": {
    "max_threads_per_user": 10,
    "default_ttl": 86400.0
  },
  "api": {
    "host": "0.0.0.0",
    "port": 5000,
    "cors_enabled": true
  },
  "performance": {
    "cache_size": 10000,
    "load_balancing_strategy": "predictive"
  }
}
```

Environment variables:
- `AIM_LOG_LEVEL`: Set logging level
- `AIM_API_HOST`: Set API host
- `AIM_API_PORT`: Set API port
- `AIM_CACHE_SIZE`: Set cache size

## Testing

The AIM Framework includes comprehensive testing capabilities:

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=aim tests/ --cov-report=html

# Run specific test categories
pytest tests/test_api_client.py -v
pytest tests/test_api_server.py -v

# Run performance tests
python -m aim.utils.performance_test --url http://localhost:5000 --concurrent-users 10
```

### Test Categories

- **Unit Tests**: Core functionality and individual components
- **Integration Tests**: API endpoints and agent interactions
- **Performance Tests**: Load testing and benchmarking
- **Security Tests**: Authentication and authorization
- **End-to-End Tests**: Complete workflow validation

### Performance Benchmarks

The framework includes built-in performance testing:

```bash
# Basic load test
aim-benchmark --benchmark-type latency --num-requests 100

# Stress test with multiple concurrent users
aim-benchmark --benchmark-type stress --concurrent-users 50 --duration 60

# Comprehensive benchmark suite
python -m aim.utils.performance_test --benchmark-all
```

**Typical Performance Metrics:**
- **Latency**: < 100ms for simple requests, < 500ms for complex multi-agent requests
- **Throughput**: 1000+ requests/second on standard hardware
- **Concurrency**: Supports 100+ concurrent users
- **Memory Usage**: < 512MB base memory footprint
- **CPU Efficiency**: Optimized for multi-core systems

### Continuous Integration

The project includes GitHub Actions workflows for:
- Automated testing on multiple Python versions
- Code quality checks with pre-commit hooks
- Security scanning with CodeQL
- Performance regression testing
- Automated deployment to staging environments

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Clone the repository
2. Install development dependencies: `pip install -e ".[dev]"`
3. Install pre-commit hooks: `pre-commit install`
4. Run tests: `pytest`

## Documentation

Full documentation is available at [https://aim-framework.readthedocs.io/](https://aim-framework.readthedocs.io/)

### Building Documentation Locally

```bash
cd docs/
make html
```

## Performance

The AIM Framework is designed for high performance and scalability:

- **Latency**: Sub-second response times for most requests
- **Throughput**: Handles thousands of concurrent requests
- **Scalability**: Horizontal scaling through agent mesh architecture
- **Memory**: Efficient memory usage with intelligent caching
- **CPU**: Optimized for multi-core systems

## Roadmap

### Version 1.1 (Q2 2024)
- [ ] Enhanced Intent Graph with machine learning capabilities
- [ ] Support for additional agent types (Image Processing, Audio Analysis)
- [ ] Advanced security features (OAuth2, SAML integration)
- [ ] Real-time collaboration features
- [ ] Plugin system for third-party extensions

### Version 1.2 (Q3 2024)
- [ ] Distributed deployment across multiple nodes
- [ ] Integration with popular AI/ML frameworks (TensorFlow, PyTorch)
- [ ] Advanced monitoring and alerting
- [ ] Multi-tenant support
- [ ] GraphQL API support

### Version 2.0 (Q4 2024)
- [ ] Complete rewrite with improved performance
- [ ] Native support for edge computing
- [ ] Advanced AI orchestration capabilities
- [ ] Enterprise features and support
- [ ] Mobile SDK for iOS and Android

### Long-term Goals
- [ ] Quantum computing integration
- [ ] Autonomous agent evolution
- [ ] Cross-platform deployment tools
- [ ] Advanced analytics and insights
- [ ] Community marketplace for agents

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support and Community

### Getting Help

- **Documentation**: [https://aim-framework.readthedocs.io/](https://aim-framework.readthedocs.io/)
- **API Reference**: [https://api.aim-framework.dev/](https://api.aim-framework.dev/)
- **Tutorials**: [https://tutorials.aim-framework.dev/](https://tutorials.aim-framework.dev/)
- **FAQ**: [https://faq.aim-framework.dev/](https://faq.aim-framework.dev/)

### Community Channels

- **GitHub Issues**: [Report bugs and request features](https://github.com/jasonviipers/aim-framework/issues)
- **GitHub Discussions**: [Community discussions and Q&A](https://github.com/jasonviipers/aim-framework/discussions)
- **Discord**: [Join our community chat](https://discord.gg/aim-framework)
- **Stack Overflow**: Use the `aim-framework` tag
- **Reddit**: [r/AIMFramework](https://reddit.com/r/AIMFramework)

### Professional Support

For enterprise customers and professional support:

- **Email**: enterprise@aimframework.com
- **Support Portal**: [https://support.aim-framework.dev/](https://support.aim-framework.dev/)
- **Training**: Custom training and workshops available
- **Consulting**: Architecture and implementation consulting

### Contributing

We welcome contributions from the community! See our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code contributions and pull requests
- Bug reports and feature requests
- Documentation improvements
- Community support and mentoring
- Translation and localization

### Security

For security vulnerabilities, please email security@aimframework.com instead of using public issues.

## Citation

If you use the AIM Framework in your research, please cite:

```bibtex
@software{aim_framework,
  title={AIM Framework: Adaptive Intelligence Mesh},
  author={jasonviipers},
  year={2025},
  url={https://github.com/jasonviipers/aim-framework}
}
```

## Acknowledgments

- Thanks to all contributors and the open-source community
- Inspired by distributed systems and multi-agent architectures
- Built with modern Python async/await patterns

