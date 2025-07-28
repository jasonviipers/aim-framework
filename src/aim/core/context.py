"""
Context management module for the AIM Framework.

This module provides context threading and management capabilities,
allowing for persistent context across sessions and selective sharing
between agents.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .exceptions import ContextNotFoundError, ValidationError


@dataclass
class ContextInteraction:
    """Represents a single interaction within a context thread.

    Attributes:
        interaction_id: Unique identifier for the interaction
        request_content: The request content
        response_content: The response content
        agent_id: ID of the agent that handled the interaction
        timestamp: When the interaction occurred
        confidence: Confidence score for the interaction
        metadata: Additional metadata
    """

    interaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_content: str = ""
    response_content: str = ""
    agent_id: str = ""
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the interaction to a dictionary."""
        return {
            "interaction_id": self.interaction_id,
            "request_content": self.request_content,
            "response_content": self.response_content,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class ContextThread:
    """
    Represents a context thread that maintains conversation history
    and shared context across multiple interactions.

    Attributes:
        thread_id (str): Unique identifier for the context thread
        user_id (str): ID of the user this thread belongs to
        created_at (float): When the thread was created
        last_updated (float): When the thread was last updated
        interactions (List[ContextInteraction]): List of interactions in this thread
        shared_context (Dict[str, Any]): Shared context data
        tags (Set[str]): Tags for categorizing the thread
        is_active (bool): Whether the thread is currently active
        max_interactions (int): Maximum number of interactions to keep
        ttl (float): Time-to-live for the thread in seconds
    """

    thread_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    interactions: List[ContextInteraction] = field(default_factory=list)
    shared_context: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    is_active: bool = True
    max_interactions: int = 100
    ttl: float = 86400.0  # 24 hours

    def __post_init__(self):
        """Validate the context thread after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate the context thread parameters."""
        if not self.user_id:
            raise ValidationError("user_id", self.user_id, "User ID cannot be empty")

        if self.max_interactions <= 0:
            raise ValidationError(
                "max_interactions",
                self.max_interactions,
                "Max interactions must be positive",
            )

        if self.ttl <= 0:
            raise ValidationError("ttl", self.ttl, "TTL must be positive")

    def add_interaction(
        self,
        request_content: str,
        response_content: str,
        agent_id: str,
        confidence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a new interaction to the context thread.

        Args:
            request_content: The request content
            response_content: The response content
            agent_id: ID of the agent that handled the interaction
            confidence: Confidence score for the interaction
            metadata: Additional metadata

        Returns:
            str: ID of the created interaction
        """
        interaction = ContextInteraction(
            request_content=request_content,
            response_content=response_content,
            agent_id=agent_id,
            confidence=confidence,
            metadata=metadata or {},
        )

        self.interactions.append(interaction)
        self.last_updated = time.time()

        # Prune old interactions if we exceed the maximum
        if len(self.interactions) > self.max_interactions:
            self.interactions = self.interactions[-self.max_interactions :]

        return interaction.interaction_id

    def update_shared_context(self, updates: Dict[str, Any]) -> None:
        """
        Update the shared context with new data.

        Args:
            updates: Dictionary of updates to apply to the shared context
        """
        self.shared_context.update(updates)
        self.last_updated = time.time()

    def get_recent_interactions(self, count: int = 5) -> List[ContextInteraction]:
        """
        Get the most recent interactions.

        Args:
            count: Number of recent interactions to return

        Returns:
            List[ContextInteraction]: List of recent interactions
        """
        return self.interactions[-count:] if self.interactions else []

    def get_interactions_by_agent(self, agent_id: str) -> List[ContextInteraction]:
        """
        Get all interactions handled by a specific agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List[ContextInteraction]: List of interactions by the agent
        """
        return [
            interaction
            for interaction in self.interactions
            if interaction.agent_id == agent_id
        ]

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the context thread.

        Args:
            tag: Tag to add
        """
        self.tags.add(tag)
        self.last_updated = time.time()

    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the context thread.

        Args:
            tag: Tag to remove
        """
        self.tags.discard(tag)
        self.last_updated = time.time()

    def is_expired(self) -> bool:
        """
        Check if the context thread has expired.

        Returns:
            bool: True if the thread has expired, False otherwise
        """
        return time.time() - self.last_updated > self.ttl

    def deactivate(self) -> None:
        """Deactivate the context thread."""
        self.is_active = False
        self.last_updated = time.time()

    def activate(self) -> None:
        """Activate the context thread."""
        self.is_active = True
        self.last_updated = time.time()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the context thread.

        Returns:
            Dict[str, Any]: Summary information
        """
        return {
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "interaction_count": len(self.interactions),
            "tags": list(self.tags),
            "is_active": self.is_active,
            "is_expired": self.is_expired(),
            "age": time.time() - self.created_at,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context thread to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "interactions": [
                interaction.to_dict() for interaction in self.interactions
            ],
            "shared_context": self.shared_context,
            "tags": list(self.tags),
            "is_active": self.is_active,
            "max_interactions": self.max_interactions,
            "ttl": self.ttl,
        }


class ContextManager:
    """
    Manages context threads for the AIM Framework.

    The ContextManager is responsible for creating, updating, and maintaining
    context threads across the system. It provides methods for context
    persistence, sharing, and pruning.
    """

    def __init__(
        self, max_threads_per_user: int = 10, cleanup_interval: float = 3600.0
    ):
        """
        Initialize the context manager.

        Args:
            max_threads_per_user: Maximum number of threads per user
            cleanup_interval: Interval for cleaning up expired threads (seconds)
        """
        self.threads: Dict[str, ContextThread] = {}
        self.user_threads: Dict[str, Set[str]] = {}
        self.max_threads_per_user = max_threads_per_user
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()

    def create_thread(
        self,
        user_id: str,
        initial_context: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
        max_interactions: int = 100,
        ttl: float = 86400.0,
    ) -> str:
        """
        Create a new context thread.

        Args:
            user_id: ID of the user
            initial_context: Initial shared context
            tags: Initial tags for the thread
            max_interactions: Maximum number of interactions to keep
            ttl: Time-to-live for the thread

        Returns:
            str: ID of the created thread
        """
        thread = ContextThread(
            user_id=user_id,
            shared_context=initial_context or {},
            tags=tags or set(),
            max_interactions=max_interactions,
            ttl=ttl,
        )

        self.threads[thread.thread_id] = thread

        # Track user threads
        if user_id not in self.user_threads:
            self.user_threads[user_id] = set()
        self.user_threads[user_id].add(thread.thread_id)

        # Prune old threads if user has too many
        self._prune_user_threads(user_id)

        return thread.thread_id

    def get_thread(self, thread_id: str) -> ContextThread:
        """
        Get a context thread by ID.

        Args:
            thread_id: ID of the thread

        Returns:
            ContextThread: The context thread

        Raises:
            ContextNotFoundError: If the thread doesn't exist
        """
        if thread_id not in self.threads:
            raise ContextNotFoundError(thread_id)

        return self.threads[thread_id]

    def get_user_threads(self, user_id: str) -> List[ContextThread]:
        """
        Get all context threads for a user.

        Args:
            user_id: ID of the user

        Returns:
            List[ContextThread]: List of user's context threads
        """
        if user_id not in self.user_threads:
            return []

        return [
            self.threads[thread_id]
            for thread_id in self.user_threads[user_id]
            if thread_id in self.threads
        ]

    def update_thread_context(self, thread_id: str, updates: Dict[str, Any]) -> None:
        """
        Update the shared context of a thread.

        Args:
            thread_id: ID of the thread
            updates: Context updates to apply

        Raises:
            ContextNotFoundError: If the thread doesn't exist
        """
        thread = self.get_thread(thread_id)
        thread.update_shared_context(updates)

    def add_interaction(
        self,
        thread_id: str,
        request_content: str,
        response_content: str,
        agent_id: str,
        confidence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add an interaction to a context thread.

        Args:
            thread_id: ID of the thread
            request_content: The request content
            response_content: The response content
            agent_id: ID of the agent
            confidence: Confidence score
            metadata: Additional metadata

        Returns:
            str: ID of the created interaction

        Raises:
            ContextNotFoundError: If the thread doesn't exist
        """
        thread = self.get_thread(thread_id)
        return thread.add_interaction(
            request_content, response_content, agent_id, confidence, metadata
        )

    def delete_thread(self, thread_id: str) -> None:
        """
        Delete a context thread.

        Args:
            thread_id: ID of the thread to delete
        """
        if thread_id in self.threads:
            thread = self.threads[thread_id]
            user_id = thread.user_id

            # Remove from threads
            del self.threads[thread_id]

            # Remove from user threads
            if user_id in self.user_threads:
                self.user_threads[user_id].discard(thread_id)
                if not self.user_threads[user_id]:
                    del self.user_threads[user_id]

    def cleanup_expired_threads(self) -> int:
        """
        Clean up expired context threads.

        Returns:
            int: Number of threads cleaned up
        """
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return 0

        expired_threads = []
        for thread_id, thread in self.threads.items():
            if thread.is_expired() or not thread.is_active:
                expired_threads.append(thread_id)

        for thread_id in expired_threads:
            self.delete_thread(thread_id)

        self.last_cleanup = current_time
        return len(expired_threads)

    def _prune_user_threads(self, user_id: str) -> None:
        """
        Prune old threads for a user if they exceed the maximum.

        Args:
            user_id: ID of the user
        """
        if user_id not in self.user_threads:
            return

        user_thread_ids = list(self.user_threads[user_id])
        if len(user_thread_ids) <= self.max_threads_per_user:
            return

        # Sort by last updated time and keep the most recent
        user_threads = [
            (thread_id, self.threads[thread_id])
            for thread_id in user_thread_ids
            if thread_id in self.threads
        ]
        user_threads.sort(key=lambda x: x[1].last_updated, reverse=True)

        # Delete the oldest threads
        threads_to_delete = user_threads[self.max_threads_per_user :]
        for thread_id, _ in threads_to_delete:
            self.delete_thread(thread_id)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the context manager.

        Returns:
            Dict[str, Any]: Statistics
        """
        active_threads = sum(1 for thread in self.threads.values() if thread.is_active)
        total_interactions = sum(
            len(thread.interactions) for thread in self.threads.values()
        )

        return {
            "total_threads": len(self.threads),
            "active_threads": active_threads,
            "total_users": len(self.user_threads),
            "total_interactions": total_interactions,
            "average_interactions_per_thread": (
                total_interactions / len(self.threads) if self.threads else 0
            ),
            "last_cleanup": self.last_cleanup,
        }
