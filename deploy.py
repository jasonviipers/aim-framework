#!/usr/bin/env python3
"""
Deployment script for the AIM Framework.

This script automates the deployment process including environment setup,
configuration validation, and service management.
"""

import os
import sys
import json
import subprocess
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentManager:
    """Manages AIM Framework deployment operations."""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.deployment_config = self._load_deployment_config()
    
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration."""
        config_file = self.config_dir / f"{self.environment}.json"
        
        if not config_file.exists():
            logger.warning(f"No config file found for {self.environment}, using defaults")
            return self._get_default_config()
        
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default deployment configuration."""
        return {
            "framework": {
                "name": "AIM Framework",
                "version": "1.0.0",
                "environment": self.environment
            },
            "api": {
                "host": "0.0.0.0",
                "port": 5000,
                "workers": 4
            },
            "deployment": {
                "method": "docker",
                "auto_restart": True,
                "health_check": True,
                "backup_enabled": True
            }
        }
    
    def validate_environment(self) -> bool:
        """Validate the deployment environment."""
        logger.info("Validating deployment environment...")
        
        checks = [
            self._check_python_version(),
            self._check_dependencies(),
            self._check_configuration(),
            self._check_permissions(),
            self._check_ports()
        ]
        
        if all(checks):
            logger.info("✓ Environment validation passed")
            return True
        else:
            logger.error("✗ Environment validation failed")
            return False
    
    def _check_python_version(self) -> bool:
        """Check Python version compatibility."""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            logger.info(f"✓ Python {version.major}.{version.minor} is compatible")
            return True
        else:
            logger.error(f"✗ Python {version.major}.{version.minor} is not supported (requires 3.8+)")
            return False
    
    def _check_dependencies(self) -> bool:
        """Check if all dependencies are available."""
        try:
            import flask
            import aiohttp
            import asyncio
            logger.info("✓ Core dependencies are available")
            return True
        except ImportError as e:
            logger.error(f"✗ Missing dependency: {e}")
            return False
    
    def _check_configuration(self) -> bool:
        """Validate configuration files."""
        required_configs = ["api", "framework"]
        
        for config_key in required_configs:
            if config_key not in self.deployment_config:
                logger.error(f"✗ Missing configuration section: {config_key}")
                return False
        
        logger.info("✓ Configuration is valid")
        return True
    
    def _check_permissions(self) -> bool:
        """Check file and directory permissions."""
        try:
            # Check if we can write to log directory
            log_dir = Path("/app/logs") if self.environment == "production" else Path("./logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write permission
            test_file = log_dir / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            logger.info("✓ File permissions are correct")
            return True
        except Exception as e:
            logger.error(f"✗ Permission error: {e}")
            return False
    
    def _check_ports(self) -> bool:
        """Check if required ports are available."""
        import socket
        
        port = self.deployment_config.get("api", {}).get("port", 5000)
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
            logger.info(f"✓ Port {port} is available")
            return True
        except OSError:
            logger.error(f"✗ Port {port} is already in use")
            return False
    
    def setup_directories(self):
        """Create necessary directories for deployment."""
        logger.info("Setting up directories...")
        
        directories = [
            "logs",
            "data",
            "temp",
            "backups"
        ]
        
        base_path = Path("/app") if self.environment == "production" else Path(".")
        
        for directory in directories:
            dir_path = base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Created directory: {dir_path}")
    
    def install_dependencies(self):
        """Install Python dependencies."""
        logger.info("Installing dependencies...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            logger.error("requirements.txt not found")
            return False
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], check=True, capture_output=True, text=True)
            logger.info("✓ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to install dependencies: {e}")
            return False
    
    def generate_systemd_service(self) -> str:
        """Generate systemd service file for production deployment."""
        service_content = f"""[Unit]
Description=AIM Framework API Server
After=network.target

[Service]
Type=exec
User=aim
Group=aim
WorkingDirectory=/app
Environment=PATH=/app/venv/bin
Environment=AIM_CONFIG_FILE=/app/config/{self.environment}.json
Environment=AIM_LOG_LEVEL=INFO
ExecStart=/app/venv/bin/gunicorn --bind 0.0.0.0:{self.deployment_config['api']['port']} --workers {self.deployment_config['api'].get('workers', 4)} --worker-class aiohttp.GunicornWebWorker aim.api.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        return service_content
    
    def deploy_docker(self):
        """Deploy using Docker."""
        logger.info("Deploying with Docker...")
        
        # Build Docker image
        try:
            subprocess.run([
                "docker", "build", "-t", "aim-framework:latest", "."
            ], check=True, cwd=self.project_root)
            logger.info("✓ Docker image built successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to build Docker image: {e}")
            return False
        
        # Run Docker container
        try:
            port = self.deployment_config['api']['port']
            subprocess.run([
                "docker", "run", "-d",
                "--name", "aim-framework",
                "-p", f"{port}:{port}",
                "-v", f"{self.config_dir}:/app/config",
                "-v", "aim-logs:/app/logs",
                "-v", "aim-data:/app/data",
                "--restart", "unless-stopped",
                "aim-framework:latest"
            ], check=True)
            logger.info("✓ Docker container started successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to start Docker container: {e}")
            return False
    
    def deploy_systemd(self):
        """Deploy using systemd service."""
        logger.info("Deploying with systemd...")
        
        # Generate service file
        service_content = self.generate_systemd_service()
        service_file = Path("/etc/systemd/system/aim-framework.service")
        
        try:
            service_file.write_text(service_content)
            logger.info("✓ Systemd service file created")
        except PermissionError:
            logger.error("✗ Permission denied writing systemd service file (run as root)")
            return False
        
        # Reload systemd and start service
        try:
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", "aim-framework"], check=True)
            subprocess.run(["systemctl", "start", "aim-framework"], check=True)
            logger.info("✓ Systemd service started successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to start systemd service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Perform health check on deployed service."""
        logger.info("Performing health check...")
        
        import requests
        import time
        
        host = self.deployment_config['api']['host']
        port = self.deployment_config['api']['port']
        url = f"http://{host}:{port}/health"
        
        # Wait for service to start
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info("✓ Health check passed")
                    return True
            except requests.RequestException:
                pass
            
            logger.info(f"Waiting for service... ({attempt + 1}/{max_attempts})")
            time.sleep(2)
        
        logger.error("✗ Health check failed")
        return False
    
    def create_backup(self):
        """Create backup of current deployment."""
        logger.info("Creating backup...")
        
        import tarfile
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"aim_backup_{timestamp}.tar.gz"
        backup_path = Path("backups") / backup_name
        
        backup_path.parent.mkdir(exist_ok=True)
        
        try:
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add("config", arcname="config")
                tar.add("logs", arcname="logs")
                if Path("data").exists():
                    tar.add("data", arcname="data")
            
            logger.info(f"✓ Backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"✗ Failed to create backup: {e}")
            return None
    
    def deploy(self, method: Optional[str] = None):
        """Main deployment method."""
        logger.info(f"Starting deployment for {self.environment} environment")
        
        # Validate environment
        if not self.validate_environment():
            logger.error("Environment validation failed, aborting deployment")
            return False
        
        # Setup directories
        self.setup_directories()
        
        # Install dependencies
        if not self.install_dependencies():
            logger.error("Dependency installation failed, aborting deployment")
            return False
        
        # Create backup if in production
        if self.environment == "production":
            self.create_backup()
        
        # Deploy based on method
        deployment_method = method or self.deployment_config.get("deployment", {}).get("method", "docker")
        
        if deployment_method == "docker":
            success = self.deploy_docker()
        elif deployment_method == "systemd":
            success = self.deploy_systemd()
        else:
            logger.error(f"Unknown deployment method: {deployment_method}")
            return False
        
        if not success:
            logger.error("Deployment failed")
            return False
        
        # Health check
        if self.deployment_config.get("deployment", {}).get("health_check", True):
            if not self.health_check():
                logger.error("Health check failed after deployment")
                return False
        
        logger.info("🎉 Deployment completed successfully!")
        return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="AIM Framework Deployment Manager")
    parser.add_argument("--environment", "-e", default="production",
                       choices=["development", "staging", "production"],
                       help="Deployment environment")
    parser.add_argument("--method", "-m", choices=["docker", "systemd"],
                       help="Deployment method")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate environment, don't deploy")
    parser.add_argument("--backup", action="store_true",
                       help="Create backup only")
    parser.add_argument("--health-check", action="store_true",
                       help="Perform health check only")
    
    args = parser.parse_args()
    
    manager = DeploymentManager(args.environment)
    
    if args.validate_only:
        success = manager.validate_environment()
        sys.exit(0 if success else 1)
    
    if args.backup:
        backup_path = manager.create_backup()
        sys.exit(0 if backup_path else 1)
    
    if args.health_check:
        success = manager.health_check()
        sys.exit(0 if success else 1)
    
    # Full deployment
    success = manager.deploy(args.method)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()