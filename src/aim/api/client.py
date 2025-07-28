"""
REST API client for the AIM Framework.

This module provides a Python client for interacting with
the AIM Framework REST API.
"""

import json
import requests
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger


class AIMClient:
    """
    Client for interacting with the AIM Framework REST API.
    
    Provides methods for sending requests, managing contexts,
    and retrieving metrics from a remote AIM Framework instance.
    """
    
    def __init__(self, base_url: str = "http://localhost:5000", timeout: float = 30.0):
        """
        Initialize the AIM client.
        
        Args:
            base_url: Base URL of the AIM Framework API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = get_logger(__name__)
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the AIM Framework server.
        
        Returns:
            Dict[str, Any]: Health status information
            
        Raises:
            requests.RequestException: If the request fails
        """
        response = self.session.get(
            f"{self.base_url}/health",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def process_request(
        self,
        user_id: str,
        content: str,
        task_type: str,
        priority: str = "normal",
        timeout: Optional[float] = None,
        context_thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a request through the AIM Framework.
        
        Args:
            user_id: ID of the user making the request
            content: Request content
            task_type: Type of task to perform
            priority: Request priority (low, normal, high, urgent)
            timeout: Request timeout (uses client default if None)
            context_thread_id: Optional context thread ID
            metadata: Optional metadata dictionary
            
        Returns:
            Dict[str, Any]: Response from the framework
            
        Raises:
            requests.RequestException: If the request fails
        """
        data = {
            "user_id": user_id,
            "content": content,
            "task_type": task_type,
            "priority": priority,
        }
        
        if timeout is not None:
            data["timeout"] = timeout
        
        if context_thread_id is not None:
            data["context_thread_id"] = context_thread_id
        
        if metadata is not None:
            data["metadata"] = metadata
        
        response = self.session.post(
            f"{self.base_url}/process",
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all registered agents.
        
        Returns:
            List[Dict[str, Any]]: List of agent information
            
        Raises:
            requests.RequestException: If the request fails
        """
        response = self.session.get(
            f"{self.base_url}/agents",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()["agents"]
    
    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get information about a specific agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dict[str, Any]: Agent information
            
        Raises:
            requests.RequestException: If the request fails
        """
        response = self.session.get(
            f"{self.base_url}/agents/{agent_id}",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def create_context_thread(
        self,
        user_id: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new context thread.
        
        Args:
            user_id: ID of the user
            initial_context: Optional initial context data
            
        Returns:
            str: ID of the created context thread
            
        Raises:
            requests.RequestException: If the request fails
        """
        data = {"user_id": user_id}
        
        if initial_context is not None:
            data["initial_context"] = initial_context
        
        response = self.session.post(
            f"{self.base_url}/context",
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()["thread_id"]
    
    def get_context_thread(self, thread_id: str) -> Dict[str, Any]:
        """
        Get a context thread.
        
        Args:
            thread_id: ID of the context thread
            
        Returns:
            Dict[str, Any]: Context thread information
            
        Raises:
            requests.RequestException: If the request fails
        """
        response = self.session.get(
            f"{self.base_url}/context/{thread_id}",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_user_context_threads(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all context threads for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List[Dict[str, Any]]: List of context thread summaries
            
        Raises:
            requests.RequestException: If the request fails
        """
        response = self.session.get(
            f"{self.base_url}/users/{user_id}/contexts",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()["contexts"]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Dict[str, Any]: Performance metrics
            
        Raises:
            requests.RequestException: If the request fails
        """
        response = self.session.get(
            f"{self.base_url}/metrics",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_framework_status(self) -> Dict[str, Any]:
        """
        Get framework status.
        
        Returns:
            Dict[str, Any]: Framework status information
            
        Raises:
            requests.RequestException: If the request fails
        """
        response = self.session.get(
            f"{self.base_url}/status",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_intent_predictions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get intent predictions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List[Dict[str, Any]]: List of predicted intents
            
        Raises:
            requests.RequestException: If the request fails
        """
        response = self.session.get(
            f"{self.base_url}/intents/{user_id}/predictions",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()["predictions"]
    
    def close(self) -> None:
        """Close the client session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

