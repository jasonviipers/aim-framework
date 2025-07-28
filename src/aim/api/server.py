"""
REST API server for the AIM Framework.

This module provides a Flask-based REST API for interacting with
the AIM Framework remotely.
"""

import asyncio
import json
from typing import Any, Dict, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS

from ..core.framework import AIMFramework
from ..core.request import Request, Priority
from ..utils.config import Config
from ..utils.logger import get_logger, setup_logging


class AIMServer:
    """
    REST API server for the AIM Framework.
    
    Provides HTTP endpoints for interacting with the framework,
    including request processing, agent management, and metrics.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the AIM server.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Create Flask app
        self.app = Flask(__name__)
        
        # Enable CORS if configured
        if config.get("api.cors_enabled", True):
            CORS(self.app, origins=config.get("security.allowed_origins", ["*"]))
        
        # Initialize framework
        self.framework = AIMFramework(config)
        
        # Setup routes
        self._setup_routes()
        
        # Server configuration
        self.host = config.get("api.host", "0.0.0.0")
        self.port = config.get("api.port", 5000)
        self.debug = config.get("api.debug", False)
    
    def _setup_routes(self) -> None:
        """Setup Flask routes."""
        
        @self.app.route("/health", methods=["GET"])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "framework_initialized": self.framework.is_initialized,
                "timestamp": self.framework.get_framework_status()
            })
        
        @self.app.route("/process", methods=["POST"])
        def process_request():
            """Process a request through the framework."""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400
                
                # Validate required fields
                required_fields = ["user_id", "content", "task_type"]
                for field in required_fields:
                    if field not in data:
                        return jsonify({"error": f"Missing required field: {field}"}), 400
                
                # Create request
                aim_request = Request(
                    user_id=data["user_id"],
                    content=data["content"],
                    task_type=data["task_type"],
                    priority=Priority(data.get("priority", "normal")),
                    timeout=data.get("timeout", 30.0),
                    context_thread_id=data.get("context_thread_id"),
                    metadata=data.get("metadata", {})
                )
                
                # Process request asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    response = loop.run_until_complete(
                        self.framework.process_request(aim_request)
                    )
                    return jsonify(response.to_dict())
                finally:
                    loop.close()
                
            except Exception as e:
                self.logger.error(f"Error processing request: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/agents", methods=["GET"])
        def list_agents():
            """List all registered agents."""
            try:
                agents = self.framework.list_agents()
                return jsonify({"agents": agents})
            except Exception as e:
                self.logger.error(f"Error listing agents: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/agents/<agent_id>", methods=["GET"])
        def get_agent(agent_id: str):
            """Get information about a specific agent."""
            try:
                agent = self.framework.get_agent(agent_id)
                return jsonify(agent.get_info())
            except Exception as e:
                self.logger.error(f"Error getting agent {agent_id}: {e}")
                return jsonify({"error": str(e)}), 404
        
        @self.app.route("/context", methods=["POST"])
        def create_context():
            """Create a new context thread."""
            try:
                data = request.get_json()
                
                if not data or "user_id" not in data:
                    return jsonify({"error": "user_id is required"}), 400
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    thread_id = loop.run_until_complete(
                        self.framework.create_context_thread(
                            user_id=data["user_id"],
                            initial_context=data.get("initial_context")
                        )
                    )
                    return jsonify({"thread_id": thread_id})
                finally:
                    loop.close()
                
            except Exception as e:
                self.logger.error(f"Error creating context: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/context/<thread_id>", methods=["GET"])
        def get_context(thread_id: str):
            """Get a context thread."""
            try:
                context = self.framework.get_context_thread(thread_id)
                return jsonify(context)
            except Exception as e:
                self.logger.error(f"Error getting context {thread_id}: {e}")
                return jsonify({"error": str(e)}), 404
        
        @self.app.route("/users/<user_id>/contexts", methods=["GET"])
        def get_user_contexts(user_id: str):
            """Get all context threads for a user."""
            try:
                contexts = self.framework.get_user_context_threads(user_id)
                return jsonify({"contexts": contexts})
            except Exception as e:
                self.logger.error(f"Error getting contexts for user {user_id}: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/metrics", methods=["GET"])
        def get_metrics():
            """Get performance metrics."""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    metrics = loop.run_until_complete(
                        self.framework.get_performance_metrics()
                    )
                    return jsonify(metrics)
                finally:
                    loop.close()
                
            except Exception as e:
                self.logger.error(f"Error getting metrics: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/status", methods=["GET"])
        def get_status():
            """Get framework status."""
            try:
                status = self.framework.get_framework_status()
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Error getting status: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/intents/<user_id>/predictions", methods=["GET"])
        def get_intent_predictions(user_id: str):
            """Get intent predictions for a user."""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    predictions = loop.run_until_complete(
                        self.framework.get_intent_predictions(user_id)
                    )
                    return jsonify({"predictions": predictions})
                finally:
                    loop.close()
                
            except Exception as e:
                self.logger.error(f"Error getting intent predictions for user {user_id}: {e}")
                return jsonify({"error": str(e)}), 500
    
    async def run(self) -> None:
        """Run the server."""
        # Initialize framework
        await self.framework.initialize()
        
        self.logger.info(f"Starting AIM server on {self.host}:{self.port}")
        
        try:
            # Run Flask app
            self.app.run(
                host=self.host,
                port=self.port,
                debug=self.debug,
                threaded=True
            )
        except KeyboardInterrupt:
            self.logger.info("Server interrupted by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            # Shutdown framework
            await self.framework.shutdown()
            self.logger.info("Server shutdown complete")

