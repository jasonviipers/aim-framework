"""
Adaptive resource scaling module for the AIM Framework.

This module implements adaptive resource scaling that automatically
adjusts the number of agents based on demand patterns and performance metrics.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from ..core.agent import Agent, AgentStatus
from ..utils.config import Config
from ..utils.logger import get_logger


class AdaptiveResourceScaler:
    """
    Manages adaptive scaling of agent resources based on demand.
    
    The AdaptiveResourceScaler monitors system performance and automatically
    scales agent resources up or down based on configurable thresholds.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the adaptive resource scaler.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.agents: Dict[str, Agent] = {}
        self.scale_up_threshold = config.get("scaling.scale_up_threshold", 0.8)
        self.scale_down_threshold = config.get("scaling.scale_down_threshold", 0.3)
        self.min_idle_time = config.get("scaling.min_idle_time", 300.0)
        self.max_scale_factor = config.get("scaling.max_scale_factor", 2.0)
        self.evaluation_interval = config.get("scaling.evaluation_interval", 30.0)
        
    async def initialize(self) -> None:
        """Initialize the resource scaler."""
        self.logger.info("Adaptive resource scaler initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the resource scaler."""
        self.logger.info("Adaptive resource scaler shutdown")
    
    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent with the scaler.
        
        Args:
            agent: Agent to register
        """
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent {agent.agent_id} with scaler")
    
    def deregister_agent(self, agent_id: str) -> None:
        """
        Deregister an agent from the scaler.
        
        Args:
            agent_id: ID of the agent to deregister
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.logger.info(f"Deregistered agent {agent_id} from scaler")
    
    async def evaluate_scaling_needs(self) -> Dict[str, Any]:
        """
        Evaluate current scaling needs and take action.
        
        Returns:
            Dict[str, Any]: Scaling evaluation results
        """
        current_time = time.time()
        
        # Calculate system metrics
        total_agents = len(self.agents)
        active_agents = sum(1 for agent in self.agents.values() if agent.status == AgentStatus.ACTIVE)
        busy_agents = sum(1 for agent in self.agents.values() if agent.status == AgentStatus.BUSY)
        idle_agents = sum(1 for agent in self.agents.values() if agent.status == AgentStatus.IDLE)
        
        if total_agents == 0:
            return {"action": "none", "reason": "no_agents"}
        
        # Calculate utilization
        utilization = busy_agents / total_agents if total_agents > 0 else 0
        
        scaling_action = "none"
        reason = "within_thresholds"
        
        # Check for scale up conditions
        if utilization > self.scale_up_threshold:
            scaling_action = "scale_up"
            reason = f"utilization_{utilization:.2f}_above_threshold_{self.scale_up_threshold}"
            await self._scale_up()
        
        # Check for scale down conditions
        elif utilization < self.scale_down_threshold:
            # Check if agents have been idle long enough
            idle_long_enough = await self._check_idle_time()
            if idle_long_enough:
                scaling_action = "scale_down"
                reason = f"utilization_{utilization:.2f}_below_threshold_{self.scale_down_threshold}"
                await self._scale_down()
        
        return {
            "action": scaling_action,
            "reason": reason,
            "metrics": {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "busy_agents": busy_agents,
                "idle_agents": idle_agents,
                "utilization": utilization,
            }
        }
    
    async def _scale_up(self) -> None:
        """Scale up agent resources."""
        # In a real implementation, this would create new agent instances
        # For now, we'll activate hibernating agents
        hibernating_agents = [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.HIBERNATING
        ]
        
        if hibernating_agents:
            agent_to_activate = hibernating_agents[0]
            agent_to_activate.activate()
            self.logger.info(f"Activated hibernating agent {agent_to_activate.agent_id}")
        else:
            self.logger.info("No hibernating agents available for activation")
    
    async def _scale_down(self) -> None:
        """Scale down agent resources."""
        # Find idle agents to hibernate
        idle_agents = [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.IDLE
        ]
        
        if idle_agents:
            # Hibernate the least recently used idle agent
            agent_to_hibernate = min(
                idle_agents,
                key=lambda a: a.metrics.last_active_time
            )
            agent_to_hibernate.hibernate()
            self.logger.info(f"Hibernated idle agent {agent_to_hibernate.agent_id}")
        else:
            self.logger.info("No idle agents available for hibernation")
    
    async def _check_idle_time(self) -> bool:
        """
        Check if idle agents have been idle long enough for scaling down.
        
        Returns:
            bool: True if agents have been idle long enough
        """
        current_time = time.time()
        idle_agents = [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.IDLE
        ]
        
        if not idle_agents:
            return False
        
        # Check if any idle agent has been idle for the minimum time
        for agent in idle_agents:
            idle_time = current_time - agent.metrics.last_active_time
            if idle_time >= self.min_idle_time:
                return True
        
        return False
    
    def get_scaling_metrics(self) -> Dict[str, Any]:
        """
        Get current scaling metrics.
        
        Returns:
            Dict[str, Any]: Scaling metrics
        """
        total_agents = len(self.agents)
        status_counts = {}
        
        for status in AgentStatus:
            count = sum(1 for agent in self.agents.values() if agent.status == status)
            status_counts[status.value] = count
        
        utilization = (
            status_counts.get("busy", 0) / total_agents
            if total_agents > 0 else 0
        )
        
        return {
            "total_agents": total_agents,
            "status_counts": status_counts,
            "utilization": utilization,
            "scale_up_threshold": self.scale_up_threshold,
            "scale_down_threshold": self.scale_down_threshold,
            "min_idle_time": self.min_idle_time,
        }

