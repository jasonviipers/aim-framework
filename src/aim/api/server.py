"""
REST API server for the AIM Framework.

This module provides a Flask-based REST API for interacting with
the AIM Framework remotely.
"""

import asyncio
import time
from functools import wraps
from typing import Dict, Any

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from ..core.framework import AIMFramework
from ..core.request import Priority, Request
from ..utils.config import Config
from ..utils.logger import get_logger


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
        
        # Configure security headers
        self._configure_security_headers()

        # Enable CORS if configured
        if config.get("api.cors_enabled", True):
            CORS(self.app, origins=config.get("security.allowed_origins", ["*"]))

        # Setup rate limiting
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=[config.get("security.rate_limit.requests_per_minute", "60/minute")]
        )

        # Initialize framework
        self.framework = AIMFramework(config)

        # Setup routes
        self._setup_routes()

        # Server configuration
        self.host = config.get("api.host", "0.0.0.0")
        self.port = config.get("api.port", 5000)
        self.debug = config.get("api.debug", False)

    def _configure_security_headers(self) -> None:
        """Configure security headers for all responses."""
        @self.app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
            return response

    def _validate_request_data(self, required_fields: list) -> tuple:
        """
        Validate request data and return data or error response.
        
        Args:
            required_fields: List of required field names
            
        Returns:
            Tuple of (data, error_response)
        """
        try:
            data = request.get_json()
            if not data:
                return None, (jsonify({"error": "No JSON data provided"}), 400)

            # Validate required fields
            for field in required_fields:
                if field not in data:
                    return None, (jsonify({"error": f"Missing required field: {field}"}), 400)

            return data, None
        except Exception as e:
            self.logger.error(f"Request validation error: {e}")
            return None, (jsonify({"error": "Invalid JSON data"}), 400)

    def _handle_async_request(self, coro):
        """
        Handle async operations in Flask routes.
        
        Args:
            coro: Coroutine to execute
            
        Returns:
            Result of the coroutine
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def _log_request(self):
        """Log request details for monitoring."""
        g.start_time = time.time()
        self.logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

    def _log_response(self, response):
        """Log response details for monitoring."""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            self.logger.info(f"Response: {response.status_code} in {duration:.3f}s")
        return response

    def _setup_routes(self) -> None:
        """Setup Flask routes."""
        
        # Add request/response logging
        self.app.before_request(self._log_request)
        self.app.after_request(self._log_response)

        @self.app.route("/health", methods=["GET"])
        def health_check():
            """Health check endpoint."""
            try:
                return jsonify(
                    {
                        "status": "healthy",
                        "framework_initialized": self.framework.is_initialized,
                        "timestamp": self.framework.get_framework_status(),
                        "version": "1.0.0"
                    }
                )
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                return jsonify({"status": "unhealthy", "error": str(e)}), 500

        @self.app.route("/process", methods=["POST"])
        @self.limiter.limit("10/minute")
        def process_request():
            """Process a request through the framework."""
            try:
                data, error_response = self._validate_request_data(["user_id", "content", "task_type"])
                if error_response:
                    return error_response

                # Create request
                aim_request = Request(
                    user_id=data["user_id"],
                    content=data["content"],
                    task_type=data["task_type"],
                    priority=Priority(data.get("priority", "normal")),
                    timeout=data.get("timeout", 30.0),
                    context_thread_id=data.get("context_thread_id"),
                    metadata=data.get("metadata", {}),
                )

                # Process request asynchronously
                response = self._handle_async_request(
                    self.framework.process_request(aim_request)
                )
                return jsonify(response.to_dict())

            except Exception as e:
                self.logger.error(f"Error processing request: {e}")
                return jsonify({"error": "Internal server error"}), 500

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
                            initial_context=data.get("initial_context"),
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
                self.logger.error(
                    f"Error getting intent predictions for user {user_id}: {e}"
                )
                return jsonify({"error": str(e)}), 500

    async def run(self) -> None:
        """Run the server."""
        # Initialize framework
        await self.framework.initialize()

        self.logger.info(f"Starting AIM server on {self.host}:{self.port}")

        try:
            # Run Flask app
            self.app.run(
                host=self.host, port=self.port, debug=self.debug, threaded=True
            )
        except KeyboardInterrupt:
            self.logger.info("Server interrupted by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            # Shutdown framework
            await self.framework.shutdown()
            self.logger.info("Server shutdown complete")
