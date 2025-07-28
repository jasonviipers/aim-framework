"""
Intent graph module for the AIM Framework.

This module implements the Intent Graph, which builds a real-time graph
of user intentions, project contexts, and capability needs to anticipate
requirements and pre-position resources.
"""

import asyncio
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.request import Request
from ..utils.config import Config
from ..utils.logger import get_logger


class IntentNode:
    """Represents a node in the intent graph."""
    
    def __init__(self, intent_id: str, intent_type: str, content: str):
        self.intent_id = intent_id
        self.intent_type = intent_type
        self.content = content
        self.timestamp = time.time()
        self.frequency = 1
        self.connections: Dict[str, float] = {}  # intent_id -> weight
        
    def add_connection(self, target_id: str, weight: float = 1.0) -> None:
        """Add or strengthen a connection to another intent."""
        if target_id in self.connections:
            self.connections[target_id] += weight
        else:
            self.connections[target_id] = weight
    
    def decay_connections(self, decay_factor: float) -> None:
        """Apply decay to connection weights."""
        for target_id in list(self.connections.keys()):
            self.connections[target_id] *= decay_factor
            if self.connections[target_id] < 0.1:  # Remove weak connections
                del self.connections[target_id]


class IntentGraph:
    """
    Manages the intent graph for predictive resource allocation.
    
    The IntentGraph tracks user intentions and their relationships to
    predict future needs and optimize resource allocation.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the intent graph.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.max_nodes_per_user = config.get("intent_graph.max_nodes_per_user", 1000)
        self.edge_weight_decay = config.get("intent_graph.edge_weight_decay", 0.95)
        self.prediction_depth = config.get("intent_graph.prediction_depth", 3)
        self.cleanup_interval = config.get("intent_graph.cleanup_interval", 3600.0)
        
        # Graph storage
        self.user_graphs: Dict[str, Dict[str, IntentNode]] = defaultdict(dict)
        self.user_sequences: Dict[str, List[str]] = defaultdict(list)
        
    async def initialize(self) -> None:
        """Initialize the intent graph."""
        self.logger.info("Intent graph initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the intent graph."""
        self.logger.info("Intent graph shutdown")
    
    async def add_intent(self, request: Request) -> str:
        """
        Add a new intent to the graph.
        
        Args:
            request: Request representing the intent
            
        Returns:
            str: ID of the created intent node
        """
        user_id = request.user_id
        intent_id = f"{user_id}_{request.task_type}_{int(time.time())}"
        
        # Create intent node
        intent_node = IntentNode(
            intent_id=intent_id,
            intent_type=request.task_type,
            content=request.content
        )
        
        # Add to user's graph
        user_graph = self.user_graphs[user_id]
        
        # If this intent type already exists, increment frequency
        existing_intent = self._find_similar_intent(user_graph, request.task_type)
        if existing_intent:
            existing_intent.frequency += 1
            intent_id = existing_intent.intent_id
        else:
            user_graph[intent_id] = intent_node
        
        # Update sequence and connections
        await self._update_connections(user_id, intent_id)
        
        # Prune old nodes if necessary
        await self._prune_user_graph(user_id)
        
        self.logger.debug(f"Added intent {intent_id} for user {user_id}")
        return intent_id
    
    async def predict_next_intents(
        self,
        user_id: str,
        max_predictions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Predict the next likely intents for a user.
        
        Args:
            user_id: ID of the user
            max_predictions: Maximum number of predictions to return
            
        Returns:
            List[Dict[str, Any]]: List of predicted intents with probabilities
        """
        if user_id not in self.user_graphs:
            return []
        
        user_graph = self.user_graphs[user_id]
        user_sequence = self.user_sequences[user_id]
        
        if not user_sequence:
            return []
        
        # Get the most recent intent
        recent_intent_id = user_sequence[-1]
        if recent_intent_id not in user_graph:
            return []
        
        recent_intent = user_graph[recent_intent_id]
        
        # Calculate predictions based on connections
        predictions = []
        for target_id, weight in recent_intent.connections.items():
            if target_id in user_graph:
                target_intent = user_graph[target_id]
                probability = weight / sum(recent_intent.connections.values())
                
                predictions.append({
                    "intent_type": target_intent.intent_type,
                    "probability": probability,
                    "frequency": target_intent.frequency,
                    "last_seen": target_intent.timestamp,
                })
        
        # Sort by probability and return top predictions
        predictions.sort(key=lambda x: x["probability"], reverse=True)
        return predictions[:max_predictions]
    
    async def get_user_intent_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        Get intent patterns for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict[str, Any]: User's intent patterns
        """
        if user_id not in self.user_graphs:
            return {"error": "User not found"}
        
        user_graph = self.user_graphs[user_id]
        user_sequence = self.user_sequences[user_id]
        
        # Calculate intent type frequencies
        intent_types = defaultdict(int)
        for intent in user_graph.values():
            intent_types[intent.intent_type] += intent.frequency
        
        # Calculate common sequences
        common_sequences = self._find_common_sequences(user_sequence)
        
        return {
            "user_id": user_id,
            "total_intents": len(user_graph),
            "intent_type_frequencies": dict(intent_types),
            "common_sequences": common_sequences,
            "recent_sequence": user_sequence[-10:],  # Last 10 intents
        }
    
    async def cleanup_expired_intents(self) -> int:
        """
        Clean up expired intents from the graph.
        
        Returns:
            int: Number of intents cleaned up
        """
        current_time = time.time()
        max_age = 30 * 24 * 3600  # 30 days
        cleaned_count = 0
        
        for user_id in list(self.user_graphs.keys()):
            user_graph = self.user_graphs[user_id]
            
            # Remove expired intents
            expired_intents = [
                intent_id for intent_id, intent in user_graph.items()
                if current_time - intent.timestamp > max_age
            ]
            
            for intent_id in expired_intents:
                del user_graph[intent_id]
                cleaned_count += 1
            
            # Clean up sequences
            self.user_sequences[user_id] = [
                intent_id for intent_id in self.user_sequences[user_id]
                if intent_id in user_graph
            ]
            
            # Remove empty user graphs
            if not user_graph:
                del self.user_graphs[user_id]
                if user_id in self.user_sequences:
                    del self.user_sequences[user_id]
        
        # Apply decay to all connections
        await self._apply_decay()
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} expired intents")
        
        return cleaned_count
    
    def _find_similar_intent(
        self,
        user_graph: Dict[str, IntentNode],
        intent_type: str
    ) -> Optional[IntentNode]:
        """Find an existing similar intent in the user's graph."""
        for intent in user_graph.values():
            if intent.intent_type == intent_type:
                return intent
        return None
    
    async def _update_connections(self, user_id: str, intent_id: str) -> None:
        """Update connections based on intent sequence."""
        user_sequence = self.user_sequences[user_id]
        user_graph = self.user_graphs[user_id]
        
        # Add to sequence
        user_sequence.append(intent_id)
        
        # Create connections with recent intents
        if len(user_sequence) > 1:
            # Connect with the previous intent
            prev_intent_id = user_sequence[-2]
            if prev_intent_id in user_graph and intent_id in user_graph:
                user_graph[prev_intent_id].add_connection(intent_id, 1.0)
        
        # Limit sequence length
        if len(user_sequence) > 100:
            user_sequence.pop(0)
    
    async def _prune_user_graph(self, user_id: str) -> None:
        """Prune old nodes from a user's graph if it exceeds the limit."""
        user_graph = self.user_graphs[user_id]
        
        if len(user_graph) <= self.max_nodes_per_user:
            return
        
        # Sort by timestamp and remove oldest
        sorted_intents = sorted(
            user_graph.items(),
            key=lambda x: x[1].timestamp
        )
        
        # Remove oldest intents
        to_remove = len(user_graph) - self.max_nodes_per_user
        for i in range(to_remove):
            intent_id = sorted_intents[i][0]
            del user_graph[intent_id]
        
        # Clean up sequences
        self.user_sequences[user_id] = [
            intent_id for intent_id in self.user_sequences[user_id]
            if intent_id in user_graph
        ]
    
    async def _apply_decay(self) -> None:
        """Apply decay to all connection weights."""
        for user_graph in self.user_graphs.values():
            for intent in user_graph.values():
                intent.decay_connections(self.edge_weight_decay)
    
    def _find_common_sequences(self, sequence: List[str]) -> List[Tuple[List[str], int]]:
        """Find common subsequences in the intent sequence."""
        if len(sequence) < 2:
            return []
        
        # Find 2-grams and 3-grams
        sequences = defaultdict(int)
        
        # 2-grams
        for i in range(len(sequence) - 1):
            bigram = tuple(sequence[i:i+2])
            sequences[bigram] += 1
        
        # 3-grams
        for i in range(len(sequence) - 2):
            trigram = tuple(sequence[i:i+3])
            sequences[trigram] += 1
        
        # Return sequences that appear more than once
        common = [(list(seq), count) for seq, count in sequences.items() if count > 1]
        common.sort(key=lambda x: x[1], reverse=True)
        
        return common[:10]  # Top 10 common sequences
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the intent graph.
        
        Returns:
            Dict[str, Any]: Graph statistics
        """
        total_users = len(self.user_graphs)
        total_intents = sum(len(graph) for graph in self.user_graphs.values())
        total_connections = sum(
            len(intent.connections)
            for graph in self.user_graphs.values()
            for intent in graph.values()
        )
        
        return {
            "total_users": total_users,
            "total_intents": total_intents,
            "total_connections": total_connections,
            "avg_intents_per_user": total_intents / total_users if total_users > 0 else 0,
            "avg_connections_per_intent": total_connections / total_intents if total_intents > 0 else 0,
        }

