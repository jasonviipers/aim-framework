"""
Capability routing module for the AIM Framework.

This module implements dynamic capability routing, which routes requests
to the most appropriate agents based on their capabilities, confidence
scores, and current load.
"""

from typing import Any, Dict, List, Set

from ..core.agent import Agent, AgentStatus
from ..core.exceptions import CapabilityNotAvailableError
from ..core.request import Request
from ..utils.config import Config
from ..utils.logger import get_logger


class CapabilityRouter:
    """
    Routes requests to appropriate agents based on capabilities and performance.

    The CapabilityRouter analyzes incoming requests and determines the optimal
    path through the agent mesh to fulfill the request requirements.
    """

    def __init__(self, config: Config):
        """
        Initialize the capability router.

        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.agents: Dict[str, Agent] = {}
        self.capability_map: Dict[str, Set[str]] = {}
        self.routing_cache: Dict[str, List[str]] = {}
        self.cache_ttl = config.get("routing.cache_ttl", 300.0)
        self.max_routing_depth = config.get("routing.max_routing_depth", 5)

    async def initialize(self, agents: Dict[str, Agent]) -> None:
        """
        Initialize the router with available agents.

        Args:
            agents: Dictionary of available agents
        """
        self.agents = agents
        self._build_capability_map()
        self.logger.info("Capability router initialized")

    def add_agent(self, agent: Agent) -> None:
        """
        Add an agent to the router.

        Args:
            agent: Agent to add
        """
        self.agents[agent.agent_id] = agent
        self._update_capability_map(agent)
        self.logger.info(f"Added agent {agent.agent_id} to router")

    def remove_agent(self, agent_id: str) -> None:
        """
        Remove an agent from the router.

        Args:
            agent_id: ID of the agent to remove
        """
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            del self.agents[agent_id]
            self._rebuild_capability_map()
            self.logger.info(f"Removed agent {agent_id} from router")

    async def route_request(self, request: Request) -> List[str]:
        """
        Route a request to appropriate agents.

        Args:
            request: Request to route

        Returns:
            List[str]: List of agent IDs that should process the request

        Raises:
            CapabilityNotAvailableError: If no suitable agents are available
        """
        # Check cache first
        cache_key = self._get_cache_key(request)
        if cache_key in self.routing_cache:
            cached_route = self.routing_cache[cache_key]
            if self._validate_route(cached_route):
                self.logger.debug(
                    f"Using cached route for request {request.request_id}"
                )
                return cached_route

        # Find suitable agents
        suitable_agents = await self._find_suitable_agents(request)

        if not suitable_agents:
            raise CapabilityNotAvailableError(
                request.task_type,
                {"request_id": request.request_id, "user_id": request.user_id},
            )

        # Select optimal routing path
        routing_path = await self._select_optimal_path(request, suitable_agents)

        # Cache the route
        self.routing_cache[cache_key] = routing_path

        # Clean up old cache entries
        self._cleanup_cache()

        self.logger.info(
            f"Routed request {request.request_id} to agents: {routing_path}"
        )
        return routing_path

    async def _find_suitable_agents(self, request: Request) -> List[Agent]:
        """
        Find agents suitable for handling the request.

        Args:
            request: Request to find agents for

        Returns:
            List[Agent]: List of suitable agents
        """
        suitable_agents = []

        for agent in self.agents.values():
            # Check if agent is active
            if agent.status != AgentStatus.ACTIVE:
                continue

            # Check if agent can handle the request
            if not agent.can_handle_request(request):
                continue

            suitable_agents.append(agent)

        return suitable_agents

    async def _select_optimal_path(
        self, request: Request, agents: List[Agent]
    ) -> List[str]:
        """
        Select the optimal routing path from suitable agents.

        Args:
            request: Request to route
            agents: List of suitable agents

        Returns:
            List[str]: Optimal routing path (agent IDs)
        """
        # Calculate scores for each agent
        agent_scores = []
        for agent in agents:
            confidence = agent.get_confidence_score(request)
            load_factor = self._calculate_load_factor(agent)
            performance_factor = self._calculate_performance_factor(agent)

            # Combined score
            score = (
                confidence * 0.5 + (1 - load_factor) * 0.3 + performance_factor * 0.2
            )

            agent_scores.append((agent.agent_id, score))

        # Sort by score (highest first)
        agent_scores.sort(key=lambda x: x[1], reverse=True)

        # For now, return the single best agent
        # In the future, this could return multiple agents for collaboration
        return [agent_scores[0][0]] if agent_scores else []

    def _calculate_load_factor(self, agent: Agent) -> float:
        """
        Calculate the current load factor for an agent.

        Args:
            agent: Agent to calculate load for

        Returns:
            float: Load factor between 0.0 and 1.0
        """
        # Simple load calculation based on status
        if agent.status == AgentStatus.IDLE:
            return 0.0
        elif agent.status == AgentStatus.BUSY:
            return 1.0
        else:
            return 0.5

    def _calculate_performance_factor(self, agent: Agent) -> float:
        """
        Calculate the performance factor for an agent.

        Args:
            agent: Agent to calculate performance for

        Returns:
            float: Performance factor between 0.0 and 1.0
        """
        # Use success rate as performance factor
        return agent.metrics.success_rate

    def _build_capability_map(self) -> None:
        """Build a map of capabilities to agent IDs."""
        self.capability_map.clear()

        for agent_id, agent in self.agents.items():
            for capability in agent.capabilities:
                capability_name = capability.value
                if capability_name not in self.capability_map:
                    self.capability_map[capability_name] = set()
                self.capability_map[capability_name].add(agent_id)

    def _update_capability_map(self, agent: Agent) -> None:
        """Update the capability map for a single agent."""
        for capability in agent.capabilities:
            capability_name = capability.value
            if capability_name not in self.capability_map:
                self.capability_map[capability_name] = set()
            self.capability_map[capability_name].add(agent.agent_id)

    def _rebuild_capability_map(self) -> None:
        """Rebuild the entire capability map."""
        self._build_capability_map()

    def _get_cache_key(self, request: Request) -> str:
        """
        Generate a cache key for a request.

        Args:
            request: Request to generate key for

        Returns:
            str: Cache key
        """
        return f"{request.task_type}:{request.priority.value}"

    def _validate_route(self, route: List[str]) -> bool:
        """
        Validate that a cached route is still valid.

        Args:
            route: Route to validate

        Returns:
            bool: True if route is valid, False otherwise
        """
        for agent_id in route:
            if agent_id not in self.agents:
                return False
            if self.agents[agent_id].status != AgentStatus.ACTIVE:
                return False
        return True

    def _cleanup_cache(self) -> None:
        """Clean up expired cache entries."""
        # Simple cleanup - in a real implementation, you'd track timestamps
        if len(self.routing_cache) > 1000:  # Arbitrary limit
            # Remove oldest entries (simplified)
            keys_to_remove = list(self.routing_cache.keys())[:100]
            for key in keys_to_remove:
                del self.routing_cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get routing statistics.

        Returns:
            Dict[str, Any]: Routing statistics
        """
        return {
            "total_agents": len(self.agents),
            "active_agents": sum(
                1
                for agent in self.agents.values()
                if agent.status == AgentStatus.ACTIVE
            ),
            "capabilities": list(self.capability_map.keys()),
            "cache_size": len(self.routing_cache),
        }
