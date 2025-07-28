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

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=aim tests/
```

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

- [ ] Support for more agent types and capabilities
- [ ] Enhanced Intent Graph with machine learning
- [ ] Distributed deployment across multiple nodes
- [ ] Integration with popular AI/ML frameworks
- [ ] Advanced security and authentication features
- [ ] Real-time collaboration features
- [ ] Plugin system for third-party extensions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [https://aim-framework.readthedocs.io/](https://aim-framework.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/jasonviipers-ai/aim-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jasonviipers-ai/aim-framework/discussions)
- **Email**: support@jasonviipers

## Citation

If you use the AIM Framework in your research, please cite:

```bibtex
@software{aim_framework,
  title={AIM Framework: Adaptive Intelligence Mesh},
  author={jasonviipers AI},
  year={2025},
  url={https://github.com/jasonviipers-ai/aim-framework}
}
```

## Acknowledgments

- Thanks to all contributors and the open-source community
- Inspired by distributed systems and multi-agent architectures
- Built with modern Python async/await patterns

