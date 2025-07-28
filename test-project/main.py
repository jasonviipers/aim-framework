#!/usr/bin/env python3
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
