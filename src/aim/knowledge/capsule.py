"""
Knowledge capsule module for the AIM Framework.

This module defines knowledge capsules that encapsulate learned
information and can be shared between agents.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Set


@dataclass
class KnowledgeCapsule:
    """
    Encapsulates a piece of knowledge that can be shared between agents.

    A knowledge capsule contains learned information, metadata about its
    source and relevance, and methods for knowledge integration.

    Attributes:
        capsule_id (str): Unique identifier for the capsule
        content (str): The knowledge content
        knowledge_type (str): Type of knowledge (e.g., "pattern", "solution", "error")
        source_agent (str): ID of the agent that created this knowledge
        confidence (float): Confidence score for the knowledge
        relevance_tags (Set[str]): Tags indicating relevance domains
        created_at (float): Timestamp when the capsule was created
        usage_count (int): Number of times this knowledge has been used
        success_rate (float): Success rate when this knowledge is applied
        metadata (Dict[str, Any]): Additional metadata
    """

    capsule_id: str
    content: str
    knowledge_type: str
    source_agent: str
    confidence: float = 0.0
    relevance_tags: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    usage_count: int = 0
    success_rate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the knowledge capsule after initialization."""
        if not self.capsule_id:
            raise ValueError("Capsule ID cannot be empty")

        if not self.content:
            raise ValueError("Content cannot be empty")

        if not self.source_agent:
            raise ValueError("Source agent cannot be empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def add_relevance_tag(self, tag: str) -> None:
        """
        Add a relevance tag to the capsule.

        Args:
            tag: Tag to add
        """
        self.relevance_tags.add(tag)

    def remove_relevance_tag(self, tag: str) -> None:
        """
        Remove a relevance tag from the capsule.

        Args:
            tag: Tag to remove
        """
        self.relevance_tags.discard(tag)

    def record_usage(self, success: bool) -> None:
        """
        Record usage of this knowledge capsule.

        Args:
            success: Whether the usage was successful
        """
        self.usage_count += 1

        # Update success rate using exponential moving average
        if self.usage_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            alpha = 0.1  # Smoothing factor
            new_success = 1.0 if success else 0.0
            self.success_rate = alpha * new_success + (1 - alpha) * self.success_rate

    def calculate_relevance_score(self, query_tags: Set[str]) -> float:
        """
        Calculate relevance score for a given set of query tags.

        Args:
            query_tags: Set of tags to match against

        Returns:
            float: Relevance score between 0.0 and 1.0
        """
        if not self.relevance_tags or not query_tags:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(self.relevance_tags.intersection(query_tags))
        union = len(self.relevance_tags.union(query_tags))

        jaccard_similarity = intersection / union if union > 0 else 0.0

        # Weight by confidence and success rate
        weighted_score = (
            jaccard_similarity * self.confidence * (0.5 + 0.5 * self.success_rate)
        )

        return min(1.0, weighted_score)

    def is_expired(self, max_age: float) -> bool:
        """
        Check if the knowledge capsule has expired.

        Args:
            max_age: Maximum age in seconds

        Returns:
            bool: True if expired, False otherwise
        """
        return time.time() - self.created_at > max_age

    def get_quality_score(self) -> float:
        """
        Calculate an overall quality score for the capsule.

        Returns:
            float: Quality score between 0.0 and 1.0
        """
        # Base score from confidence
        base_score = self.confidence

        # Boost for usage (knowledge that's been used is more valuable)
        usage_boost = min(0.2, self.usage_count * 0.02)

        # Boost for success rate
        success_boost = self.success_rate * 0.3

        # Age penalty (newer knowledge is generally more relevant)
        age_days = (time.time() - self.created_at) / 86400
        age_penalty = max(0.0, min(0.2, age_days * 0.01))

        quality_score = base_score + usage_boost + success_boost - age_penalty

        return max(0.0, min(1.0, quality_score))

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the capsule to a dictionary for serialization.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "capsule_id": self.capsule_id,
            "content": self.content,
            "knowledge_type": self.knowledge_type,
            "source_agent": self.source_agent,
            "confidence": self.confidence,
            "relevance_tags": list(self.relevance_tags),
            "created_at": self.created_at,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "metadata": self.metadata,
            "quality_score": self.get_quality_score(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeCapsule":
        """
        Create a KnowledgeCapsule from a dictionary.

        Args:
            data: Dictionary containing capsule data

        Returns:
            KnowledgeCapsule: New capsule instance
        """
        # Convert relevance_tags back to set
        if "relevance_tags" in data and isinstance(data["relevance_tags"], list):
            data["relevance_tags"] = set(data["relevance_tags"])

        # Remove computed fields
        data.pop("quality_score", None)

        return cls(**data)

    def merge_with(self, other: "KnowledgeCapsule") -> "KnowledgeCapsule":
        """
        Merge this capsule with another capsule of the same type.

        Args:
            other: Another knowledge capsule to merge with

        Returns:
            KnowledgeCapsule: New merged capsule

        Raises:
            ValueError: If capsules are not compatible for merging
        """
        if self.knowledge_type != other.knowledge_type:
            raise ValueError("Cannot merge capsules of different types")

        # Create merged capsule
        merged_id = f"merged_{self.capsule_id}_{other.capsule_id}"
        merged_content = f"{self.content}\n\n---\n\n{other.content}"

        # Average confidence weighted by usage
        total_usage = self.usage_count + other.usage_count
        if total_usage > 0:
            merged_confidence = (
                self.confidence * self.usage_count
                + other.confidence * other.usage_count
            ) / total_usage
        else:
            merged_confidence = (self.confidence + other.confidence) / 2

        # Merge relevance tags
        merged_tags = self.relevance_tags.union(other.relevance_tags)

        # Use the more recent source agent
        source_agent = (
            self.source_agent
            if self.created_at > other.created_at
            else other.source_agent
        )

        # Merge metadata
        merged_metadata = {**self.metadata, **other.metadata}
        merged_metadata["merged_from"] = [self.capsule_id, other.capsule_id]

        return KnowledgeCapsule(
            capsule_id=merged_id,
            content=merged_content,
            knowledge_type=self.knowledge_type,
            source_agent=source_agent,
            confidence=merged_confidence,
            relevance_tags=merged_tags,
            created_at=max(self.created_at, other.created_at),
            usage_count=total_usage,
            success_rate=(self.success_rate + other.success_rate) / 2,
            metadata=merged_metadata,
        )

    def __str__(self) -> str:
        """String representation of the capsule."""
        return f"KnowledgeCapsule(id={self.capsule_id}, type={self.knowledge_type}, confidence={self.confidence:.2f})"

    def __repr__(self) -> str:
        """Detailed string representation of the capsule."""
        return (
            f"KnowledgeCapsule(capsule_id='{self.capsule_id}', "
            f"knowledge_type='{self.knowledge_type}', "
            f"source_agent='{self.source_agent}', "
            f"confidence={self.confidence}, "
            f"usage_count={self.usage_count})"
        )
