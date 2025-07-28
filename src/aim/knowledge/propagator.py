"""
Learning propagation module for the AIM Framework.

This module implements cross-agent learning propagation, allowing
knowledge gained by one agent to be shared across the mesh.
"""

import time
from typing import Any, Dict, List, Optional

from ..core.request import Response
from ..utils.config import Config
from ..utils.logger import get_logger


class LearningPropagator:
    """
    Manages learning propagation across the agent mesh.

    The LearningPropagator identifies valuable knowledge from agent
    responses and propagates it to other relevant agents in the mesh.
    """

    def __init__(self, config: Config):
        """
        Initialize the learning propagator.

        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.propagation_enabled = config.get("knowledge.propagation_enabled", True)
        self.relevance_threshold = config.get("knowledge.relevance_threshold", 0.6)
        self.max_knowledge_age = config.get(
            "knowledge.max_knowledge_age", 604800.0
        )  # 7 days
        self.cleanup_interval = config.get("knowledge.cleanup_interval", 3600.0)

        # Knowledge storage
        self.knowledge_base: List[Dict[str, Any]] = []

    async def initialize(self) -> None:
        """Initialize the learning propagator."""
        self.logger.info("Learning propagator initialized")

    async def shutdown(self) -> None:
        """Shutdown the learning propagator."""
        self.logger.info("Learning propagator shutdown")

    async def propagate_learning(self, response: Response) -> None:
        """
        Propagate learning from a response.

        Args:
            response: Response to extract learning from
        """
        if not self.propagation_enabled:
            return

        # Extract knowledge from the response
        knowledge = await self._extract_knowledge(response)

        if knowledge:
            # Store the knowledge
            await self._store_knowledge(knowledge)

            # Propagate to relevant agents
            await self._propagate_to_agents(knowledge)

    async def _extract_knowledge(self, response: Response) -> Optional[Dict[str, Any]]:
        """
        Extract knowledge from a response.

        Args:
            response: Response to extract knowledge from

        Returns:
            Optional[Dict[str, Any]]: Extracted knowledge or None
        """
        # Only extract knowledge from successful, high-confidence responses
        if not response.success or response.confidence < self.relevance_threshold:
            return None

        # Simple knowledge extraction (in practice, this would be more sophisticated)
        knowledge = {
            "id": f"knowledge_{int(time.time())}_{response.agent_id}",
            "source_agent": response.agent_id,
            "content": response.content,
            "confidence": response.confidence,
            "timestamp": time.time(),
            "metadata": response.metadata.copy(),
            "relevance_score": response.confidence,
        }

        return knowledge

    async def _store_knowledge(self, knowledge: Dict[str, Any]) -> None:
        """
        Store knowledge in the knowledge base.

        Args:
            knowledge: Knowledge to store
        """
        self.knowledge_base.append(knowledge)
        self.logger.debug(f"Stored knowledge: {knowledge['id']}")

    async def _propagate_to_agents(self, knowledge: Dict[str, Any]) -> None:
        """
        Propagate knowledge to relevant agents.

        Args:
            knowledge: Knowledge to propagate
        """
        # In a real implementation, this would identify relevant agents
        # and send the knowledge to them for integration
        self.logger.debug(f"Propagating knowledge {knowledge['id']} to relevant agents")

    async def cleanup_expired_knowledge(self) -> int:
        """
        Clean up expired knowledge from the knowledge base.

        Returns:
            int: Number of knowledge items cleaned up
        """
        current_time = time.time()
        initial_count = len(self.knowledge_base)

        # Remove expired knowledge
        self.knowledge_base = [
            knowledge
            for knowledge in self.knowledge_base
            if current_time - knowledge["timestamp"] <= self.max_knowledge_age
        ]

        cleaned_count = initial_count - len(self.knowledge_base)

        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} expired knowledge items")

        return cleaned_count

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.

        Returns:
            Dict[str, Any]: Knowledge base statistics
        """
        if not self.knowledge_base:
            return {
                "total_knowledge": 0,
                "avg_confidence": 0.0,
                "oldest_knowledge_age": 0.0,
                "newest_knowledge_age": 0.0,
            }

        current_time = time.time()
        confidences = [k["confidence"] for k in self.knowledge_base]
        timestamps = [k["timestamp"] for k in self.knowledge_base]

        return {
            "total_knowledge": len(self.knowledge_base),
            "avg_confidence": sum(confidences) / len(confidences),
            "oldest_knowledge_age": current_time - min(timestamps),
            "newest_knowledge_age": current_time - max(timestamps),
        }
