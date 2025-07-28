"""
Main command-line interface for the AIM Framework.

This module provides the main CLI entry points for the AIM Framework,
including server management, benchmarking, and initialization commands.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from ..api.server import AIMServer
from ..utils.config import Config
from ..utils.logger import get_logger, setup_logging


def start_server() -> None:
    """Start the AIM Framework server."""
    parser = argparse.ArgumentParser(description="Start the AIM Framework server")
    parser.add_argument("--config", "-c", type=str, help="Path to configuration file")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind the server to"
    )
    parser.add_argument(
        "--port", "-p", type=int, default=5000, help="Port to bind the server to"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    parser.add_argument("--log-file", type=str, help="Path to log file")

    args = parser.parse_args()

    # Load configuration
    config = Config()
    if args.config:
        config.load_from_file(args.config)

    # Override with command line arguments
    config.set("api.host", args.host)
    config.set("api.port", args.port)
    config.set("api.debug", args.debug)
    config.set("logging.level", args.log_level)
    if args.log_file:
        config.set("logging.file", args.log_file)

    # Setup logging
    setup_logging(
        level=config.get("logging.level", "INFO"),
        format_string=config.get("logging.format"),
        log_file=config.get("logging.file"),
        max_file_size=config.get("logging.max_file_size", 10485760),
        backup_count=config.get("logging.backup_count", 5),
    )

    logger = get_logger(__name__)
    logger.info("Starting AIM Framework server...")

    # Validate configuration
    errors = config.validate()
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)

    # Create and start server
    try:
        server = AIMServer(config)
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


def run_benchmark() -> None:
    """Run performance benchmarks."""
    parser = argparse.ArgumentParser(description="Run AIM Framework benchmarks")
    parser.add_argument("--config", "-c", type=str, help="Path to configuration file")
    parser.add_argument(
        "--benchmark-type",
        type=str,
        default="latency",
        choices=["latency", "throughput", "memory", "full"],
        help="Type of benchmark to run",
    )
    parser.add_argument(
        "--num-requests", type=int, default=100, help="Number of requests to send"
    )
    parser.add_argument(
        "--concurrency", type=int, default=10, help="Number of concurrent requests"
    )
    parser.add_argument(
        "--output", "-o", type=str, help="Output file for benchmark results"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Load configuration
    config = Config()
    if args.config:
        config.load_from_file(args.config)

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)

    logger = get_logger(__name__)
    logger.info("Starting AIM Framework benchmark...")

    # Import benchmark module
    try:
        from ..benchmarking import BenchmarkSuite
    except ImportError:
        logger.error("Benchmarking module not available")
        sys.exit(1)

    # Run benchmark
    try:
        benchmark = BenchmarkSuite(config)
        results = asyncio.run(
            benchmark.run_benchmark(
                benchmark_type=args.benchmark_type,
                num_requests=args.num_requests,
                concurrency=args.concurrency,
            )
        )

        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Benchmark results saved to {args.output}")
        else:
            print(json.dumps(results, indent=2))

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)


def init_framework() -> None:
    """Initialize a new AIM Framework project."""
    parser = argparse.ArgumentParser(
        description="Initialize a new AIM Framework project"
    )
    parser.add_argument("project_name", type=str, help="Name of the project to create")
    parser.add_argument(
        "--template",
        type=str,
        default="basic",
        choices=["basic", "advanced", "minimal"],
        help="Project template to use",
    )
    parser.add_argument(
        "--directory",
        "-d",
        type=str,
        default=".",
        help="Directory to create the project in",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing project directory"
    )

    args = parser.parse_args()

    setup_logging(level="INFO")
    logger = get_logger(__name__)

    project_dir = Path(args.directory) / args.project_name

    # Check if directory exists
    if project_dir.exists() and not args.force:
        logger.error(f"Project directory already exists: {project_dir}")
        logger.error("Use --force to overwrite")
        sys.exit(1)

    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Creating AIM Framework project: {args.project_name}")

    # Create project structure
    _create_project_structure(project_dir, args.template, logger)

    logger.info(f"Project created successfully in {project_dir}")
    logger.info("To get started:")
    logger.info(f"  cd {project_dir}")
    logger.info("  pip install -r requirements.txt")
    logger.info("  python main.py")


def _create_project_structure(project_dir: Path, template: str, logger) -> None:
    """Create the project directory structure."""

    # Create directories
    directories = [
        "agents",
        "config",
        "logs",
        "data",
        "tests",
    ]

    for directory in directories:
        (project_dir / directory).mkdir(exist_ok=True)

    # Create main.py
    main_py_content = '''#!/usr/bin/env python3
"""
Main entry point for the AIM Framework project.
"""

import asyncio
from aim import AIMFramework, Config
from aim.utils.logger import setup_logging

async def main():
    """Main function."""
    # Setup logging
    setup_logging(level="INFO")
    
    # Load configuration
    config = Config("config/config.json")
    
    # Create and initialize framework
    framework = AIMFramework(config)
    await framework.initialize()
    
    print("AIM Framework initialized successfully!")
    print(f"Framework status: {framework.get_framework_status()}")
    
    # Keep the framework running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        await framework.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
'''

    with open(project_dir / "main.py", "w") as f:
        f.write(main_py_content)

    # Create requirements.txt
    requirements_content = """aim-framework>=1.0.0
flask>=2.2.0
flask-cors>=4.0.0
"""

    with open(project_dir / "requirements.txt", "w") as f:
        f.write(requirements_content)

    # Create configuration file
    config_content = {
        "framework": {
            "name": f"AIM Framework Project",
            "version": "1.0.0",
            "log_level": "INFO",
        },
        "api": {"host": "0.0.0.0", "port": 5000, "debug": False},
    }

    config_dir = project_dir / "config"
    with open(config_dir / "config.json", "w") as f:
        json.dump(config_content, f, indent=2)

    # Create example agent
    agent_content = '''"""
Example agent for the AIM Framework project.
"""

from aim import Agent, AgentCapability, Request, Response

class ExampleAgent(Agent):
    """Example agent implementation."""
    
    def __init__(self):
        super().__init__(
            capabilities={AgentCapability.CODE_GENERATION},
            description="Example agent for demonstration purposes",
            version="1.0.0"
        )
    
    async def process_request(self, request: Request) -> Response:
        """Process a request and return a response."""
        # Simple echo response
        content = f"Echo: {request.content}"
        
        return Response(
            request_id=request.request_id,
            agent_id=self.agent_id,
            content=content,
            confidence=0.9,
            success=True
        )
'''

    with open(project_dir / "agents" / "example_agent.py", "w") as f:
        f.write(agent_content)

    # Create README.md
    readme_content = f"""# {project_dir.name}

AIM Framework project created with template: {template}

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the project:
   ```bash
   python main.py
   ```

## Project Structure

- `agents/` - Custom agent implementations
- `config/` - Configuration files
- `logs/` - Log files
- `data/` - Data files
- `tests/` - Test files
- `main.py` - Main entry point

## Configuration

Edit `config/config.json` to customize the framework settings.

## Adding Agents

Create new agent classes in the `agents/` directory and register them with the framework.
"""

    with open(project_dir / "README.md", "w") as f:
        f.write(readme_content)

    logger.info("Created project structure:")
    for directory in directories:
        logger.info(f"  {directory}/")
    logger.info("  main.py")
    logger.info("  requirements.txt")
    logger.info("  README.md")
    logger.info("  config/config.json")
    logger.info("  agents/example_agent.py")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AIM Framework Command Line Interface", prog="aim"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Server command
    server_parser = subparsers.add_parser(
        "server", help="Start the AIM Framework server"
    )
    server_parser.set_defaults(func=start_server)

    # Benchmark command
    benchmark_parser = subparsers.add_parser(
        "benchmark", help="Run performance benchmarks"
    )
    benchmark_parser.set_defaults(func=run_benchmark)

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new project")
    init_parser.set_defaults(func=init_framework)

    # Parse arguments
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
