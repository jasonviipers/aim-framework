"""
Main framework module for the AIM Framework.

This module contains the AIMFramework class, which is the main orchestrator
for the Adaptive Intelligence Mesh system.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from ..coordination.collaborator import ConfidenceBasedCollaborator
from ..coordination.router import CapabilityRouter
from ..knowledge.intent_graph import IntentGraph
from ..knowledge.propagator import LearningPropagator
from ..resources.monitor import PerformanceMonitor
from ..resources.scaler import AdaptiveResourceScaler
from ..utils.config import Config
from ..utils.logger import get_logger
from .agent import Agent, AgentStatus
from .context import ContextManager
from .exceptions import (
    AgentNotFoundError,
    AIMException,
    CapabilityNotAvailableError,
    ConfigurationError,
)
from .request import Request, RequestStatus, Response


class AIMFramework:
    """
    Main orchestrator class for the Adaptive Intelligence Mesh Framework.

    The AIMFramework coordinates all components of the system, including
    agents, routing, context management, resource scaling, and knowledge
    propagation.

    Attributes:
        config (Config): Framework configuration
        agents (Dict[str, Agent]): Registry of active agents
        context_manager (ContextManager): Context thread manager
        router (CapabilityRouter): Request routing component
        collaborator (ConfidenceBasedCollaborator): Agent collaboration component
        scaler (AdaptiveResourceScaler): Resource scaling component
        monitor (PerformanceMonitor): Performance monitoring component
        propagator (LearningPropagator): Knowledge propagation component
        intent_graph (IntentGraph): Intent graph component
        is_initialized (bool): Whether the framework has been initialized
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the AIM Framework.

        Args:
            config: Framework configuration. If None, default config will be used.
        """
        self.config = config or Config()
        self.logger = get_logger(__name__)

        # Core components
        self.agents: Dict[str, Agent] = {}
        self.context_manager = ContextManager(
            max_threads_per_user=self.config.get("context.max_threads_per_user", 10),
            cleanup_interval=self.config.get("context.cleanup_interval", 3600.0),
        )

        # Coordination components
        self.router = CapabilityRouter(self.config)
        self.collaborator = ConfidenceBasedCollaborator(self.config)

        # Resource management components
        self.scaler = AdaptiveResourceScaler(self.config)
        self.monitor = PerformanceMonitor(self.config)

        # Knowledge management components
        self.propagator = LearningPropagator(self.config)
        self.intent_graph = IntentGraph(self.config)

        # Framework state
        self.is_initialized = False
        self._shutdown_event = asyncio.Event()

        # Set start time
        self.config.set("framework.start_time", time.time())

        self.logger.info("AIM Framework initialized")

    async def initialize(self) -> None:
        """
        Initialize the framework and all its components.

        This method must be called before using the framework.
        """
        if self.is_initialized:
            self.logger.warning("Framework already initialized")
            return

        try:
            self.logger.info("Initializing AIM Framework components...")

            # Initialize components
            await self.router.initialize(self.agents)
            await self.collaborator.initialize()
            await self.scaler.initialize()
            await self.monitor.initialize()
            await self.propagator.initialize()
            await self.intent_graph.initialize()

            # Start background tasks
            asyncio.create_task(self._background_cleanup())
            asyncio.create_task(self._background_monitoring())
            asyncio.create_task(self._background_scaling())

            self.is_initialized = True
            self.logger.info("AIM Framework initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize AIM Framework: {e}")
            raise ConfigurationError("framework_initialization", str(e))

    async def shutdown(self) -> None:
        """
        Shutdown the framework and clean up resources.
        """
        if not self.is_initialized:
            return

        self.logger.info("Shutting down AIM Framework...")

        # Signal shutdown to background tasks
        self._shutdown_event.set()

        # Shutdown components
        await self.monitor.shutdown()
        await self.scaler.shutdown()
        await self.propagator.shutdown()
        await self.intent_graph.shutdown()

        # Deactivate all agents
        for agent in self.agents.values():
            agent.deactivate()

        self.is_initialized = False
        self.logger.info("AIM Framework shutdown complete")

    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent with the framework.

        Args:
            agent: The agent to register

        Raises:
            AIMException: If the agent is already registered
        """
        if agent.agent_id in self.agents:
            raise AIMException(f"Agent {agent.agent_id} is already registered")

        self.agents[agent.agent_id] = agent
        self.router.add_agent(agent)
        self.scaler.register_agent(agent)

        self.logger.info(f"Registered agent: {agent.agent_id}")

    def deregister_agent(self, agent_id: str) -> None:
        """
        Deregister an agent from the framework.

        Args:
            agent_id: ID of the agent to deregister

        Raises:
            AgentNotFoundError: If the agent is not found
        """
        if agent_id not in self.agents:
            raise AgentNotFoundError(agent_id)

        agent = self.agents[agent_id]
        agent.deactivate()

        self.router.remove_agent(agent_id)
        self.scaler.deregister_agent(agent_id)

        del self.agents[agent_id]

        self.logger.info(f"Deregistered agent: {agent_id}")

    def get_agent(self, agent_id: str) -> Agent:
        """
        Get an agent by ID.

        Args:
            agent_id: ID of the agent

        Returns:
            Agent: The requested agent

        Raises:
            AgentNotFoundError: If the agent is not found
        """
        if agent_id not in self.agents:
            raise AgentNotFoundError(agent_id)

        return self.agents[agent_id]

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all registered agents.

        Returns:
            List[Dict[str, Any]]: List of agent information
        """
        return [agent.get_info() for agent in self.agents.values()]

    async def process_request(self, request: Request) -> Response:
        """
        Process a request through the framework.

        This is the main entry point for processing user requests. The framework
        will route the request to appropriate agents, manage context, and return
        a response.

        Args:
            request: The request to process

        Returns:
            Response: The response from processing the request

        Raises:
            AIMException: If the request cannot be processed
        """
        if not self.is_initialized:
            raise AIMException("Framework not initialized. Call initialize() first.")

        start_time = time.time()
        request.set_status(RequestStatus.ROUTING)

        try:
            self.logger.info(
                f"Processing request {request.request_id} from user {request.user_id}"
            )

            # Update intent graph
            await self.intent_graph.add_intent(request)

            # Route the request to appropriate agents
            agent_path = await self.router.route_request(request)

            if not agent_path:
                raise CapabilityNotAvailableError(request.task_type)

            request.set_status(RequestStatus.PROCESSING)

            # Process through agent collaboration
            response = await self.collaborator.process_with_collaboration(
                request, agent_path
            )

            # Update context if thread ID is provided
            if request.context_thread_id:
                try:
                    await self._update_context_thread(request, response)
                except Exception as e:
                    self.logger.warning(f"Failed to update context thread: {e}")

            # Propagate learning
            await self.propagator.propagate_learning(response)

            # Update performance metrics
            processing_time = time.time() - start_time
            await self.monitor.record_request(request, response, processing_time)

            request.set_status(RequestStatus.COMPLETED)

            self.logger.info(
                f"Completed request {request.request_id} in {processing_time:.3f}s"
            )

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            request.set_status(RequestStatus.FAILED)

            self.logger.error(f"Failed to process request {request.request_id}: {e}")

            # Create error response
            response = Response.create_error_response(
                request_id=request.request_id,
                agent_id="framework",
                error_message=str(e),
                processing_time=processing_time,
            )

            # Still record metrics for failed requests
            await self.monitor.record_request(request, response, processing_time)

            return response

    async def create_context_thread(
        self, user_id: str, initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new context thread for a user.

        Args:
            user_id: ID of the user
            initial_context: Initial context data

        Returns:
            str: ID of the created context thread
        """
        return self.context_manager.create_thread(user_id, initial_context)

    def get_context_thread(self, thread_id: str) -> Dict[str, Any]:
        """
        Get a context thread by ID.

        Args:
            thread_id: ID of the context thread

        Returns:
            Dict[str, Any]: Context thread information
        """
        thread = self.context_manager.get_thread(thread_id)
        return thread.to_dict()

    def get_user_context_threads(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all context threads for a user.

        Args:
            user_id: ID of the user

        Returns:
            List[Dict[str, Any]]: List of context thread summaries
        """
        threads = self.context_manager.get_user_threads(user_id)
        return [thread.get_summary() for thread in threads]

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.

        Returns:
            Dict[str, Any]: Performance metrics
        """
        return await self.monitor.get_metrics()

    async def get_intent_predictions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get intent predictions for a user.

        Args:
            user_id: ID of the user

        Returns:
            List[Dict[str, Any]]: List of predicted intents
        """
        return await self.intent_graph.predict_next_intents(user_id)

    def get_framework_status(self) -> Dict[str, Any]:
        """
        Get the current status of the framework.

        Returns:
            Dict[str, Any]: Framework status information
        """
        active_agents = sum(
            1 for agent in self.agents.values() if agent.status == AgentStatus.ACTIVE
        )

        start_time = self.config.get("framework.start_time", time.time())

        return {
            "initialized": self.is_initialized,
            "total_agents": len(self.agents),
            "active_agents": active_agents,
            "context_stats": self.context_manager.get_stats(),
            "uptime": time.time() - start_time,
        }

    async def _update_context_thread(
        self, request: Request, response: Response
    ) -> None:
        """
        Update the context thread with the request and response.

        Args:
            request: The processed request
            response: The generated response
        """
        try:
            self.context_manager.add_interaction(
                thread_id=request.context_thread_id,
                request_content=request.content,
                response_content=response.content,
                agent_id=response.agent_id,
                confidence=response.confidence,
                metadata=response.metadata,
            )

            # Apply any context updates from the response
            if response.context_updates:
                self.context_manager.update_thread_context(
                    request.context_thread_id, response.context_updates
                )

        except Exception as e:
            self.logger.warning(
                f"Failed to update context thread {request.context_thread_id}: {e}"
            )

    async def _background_cleanup(self) -> None:
        """Background task for cleaning up expired resources."""
        while not self._shutdown_event.is_set():
            try:
                # Clean up expired context threads
                cleaned_threads = self.context_manager.cleanup_expired_threads()
                if cleaned_threads > 0:
                    self.logger.info(
                        f"Cleaned up {cleaned_threads} expired context threads"
                    )

                # Clean up other expired resources
                await self.intent_graph.cleanup_expired_intents()
                await self.propagator.cleanup_expired_knowledge()

            except Exception as e:
                self.logger.error(f"Error in background cleanup: {e}")

            # Wait before next cleanup cycle
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.config.get("framework.cleanup_interval", 300.0),
                )
                break  # Shutdown event was set
            except asyncio.TimeoutError:
                continue  # Continue cleanup cycle

    async def _background_monitoring(self) -> None:
        """Background task for performance monitoring."""
        while not self._shutdown_event.is_set():
            try:
                await self.monitor.collect_system_metrics()

            except Exception as e:
                self.logger.error(f"Error in background monitoring: {e}")

            # Wait before next monitoring cycle
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.config.get("monitoring.collection_interval", 60.0),
                )
                break  # Shutdown event was set
            except asyncio.TimeoutError:
                continue  # Continue monitoring cycle

    async def _background_scaling(self) -> None:
        """Background task for adaptive resource scaling."""
        while not self._shutdown_event.is_set():
            try:
                await self.scaler.evaluate_scaling_needs()

            except Exception as e:
                self.logger.error(f"Error in background scaling: {e}")

            # Wait before next scaling evaluation
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.config.get("scaling.evaluation_interval", 30.0),
                )
                break  # Shutdown event was set
            except asyncio.TimeoutError:
                continue  # Continue scaling cycle
