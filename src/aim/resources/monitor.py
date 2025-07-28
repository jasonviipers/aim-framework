"""
Performance monitoring module for the AIM Framework.

This module implements performance monitoring and metrics collection
for the framework and its agents.
"""

import asyncio
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional

from ..core.request import Request, Response
from ..utils.config import Config
from ..utils.logger import get_logger


class PerformanceMonitor:
    """
    Monitors and collects performance metrics for the AIM Framework.
    
    The PerformanceMonitor tracks various metrics including response times,
    throughput, error rates, and system resource usage.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the performance monitor.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.collection_interval = config.get("monitoring.collection_interval", 60.0)
        self.metrics_retention = config.get("monitoring.metrics_retention", 86400.0)
        self.enable_detailed_metrics = config.get("monitoring.enable_detailed_metrics", True)
        
        # Metrics storage
        self.request_metrics: deque = deque(maxlen=10000)
        self.system_metrics: deque = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.agent_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Real-time counters
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_processing_time = 0.0
        
        # Alert thresholds
        self.alert_thresholds = config.get("monitoring.alert_thresholds", {})
        
    async def initialize(self) -> None:
        """Initialize the performance monitor."""
        self.logger.info("Performance monitor initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the performance monitor."""
        self.logger.info("Performance monitor shutdown")
    
    async def record_request(
        self,
        request: Request,
        response: Response,
        processing_time: float
    ) -> None:
        """
        Record metrics for a processed request.
        
        Args:
            request: The processed request
            response: The generated response
            processing_time: Time taken to process the request
        """
        current_time = time.time()
        
        # Update counters
        self.total_requests += 1
        self.total_processing_time += processing_time
        
        if response.success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # Store detailed metrics
        if self.enable_detailed_metrics:
            metric_record = {
                "timestamp": current_time,
                "request_id": request.request_id,
                "user_id": request.user_id,
                "task_type": request.task_type,
                "agent_id": response.agent_id,
                "processing_time": processing_time,
                "confidence": response.confidence,
                "success": response.success,
                "priority": request.priority.value,
            }
            
            self.request_metrics.append(metric_record)
            self.agent_metrics[response.agent_id].append(metric_record)
        
        # Check for alerts
        await self._check_alerts(processing_time, response.success)
    
    async def collect_system_metrics(self) -> None:
        """Collect system-level metrics."""
        current_time = time.time()
        
        try:
            import psutil
            
            # Collect system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_metric = {
                "timestamp": current_time,
                "cpu_usage": cpu_usage,
                "memory_usage": memory.percent,
                "memory_available": memory.available,
                "disk_usage": disk.percent,
                "disk_free": disk.free,
            }
            
            self.system_metrics.append(system_metric)
            
        except ImportError:
            # psutil not available, use basic metrics
            system_metric = {
                "timestamp": current_time,
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "memory_available": 0,
                "disk_usage": 0.0,
                "disk_free": 0,
            }
            
            self.system_metrics.append(system_metric)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns:
            Dict[str, Any]: Current performance metrics
        """
        current_time = time.time()
        
        # Calculate rates and averages
        avg_processing_time = (
            self.total_processing_time / self.total_requests
            if self.total_requests > 0 else 0.0
        )
        
        success_rate = (
            self.successful_requests / self.total_requests
            if self.total_requests > 0 else 0.0
        )
        
        error_rate = (
            self.failed_requests / self.total_requests
            if self.total_requests > 0 else 0.0
        )
        
        # Calculate recent metrics (last 5 minutes)
        recent_metrics = self._calculate_recent_metrics(300)
        
        # Get latest system metrics
        latest_system = self.system_metrics[-1] if self.system_metrics else {}
        
        return {
            "timestamp": current_time,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "avg_processing_time": avg_processing_time,
            "recent_metrics": recent_metrics,
            "system_metrics": latest_system,
            "agent_count": len(self.agent_metrics),
        }
    
    def _calculate_recent_metrics(self, time_window: float) -> Dict[str, Any]:
        """
        Calculate metrics for a recent time window.
        
        Args:
            time_window: Time window in seconds
            
        Returns:
            Dict[str, Any]: Recent metrics
        """
        current_time = time.time()
        cutoff_time = current_time - time_window
        
        recent_requests = [
            metric for metric in self.request_metrics
            if metric["timestamp"] >= cutoff_time
        ]
        
        if not recent_requests:
            return {
                "request_count": 0,
                "avg_processing_time": 0.0,
                "success_rate": 0.0,
                "throughput": 0.0,
            }
        
        total_time = sum(req["processing_time"] for req in recent_requests)
        successful = sum(1 for req in recent_requests if req["success"])
        
        return {
            "request_count": len(recent_requests),
            "avg_processing_time": total_time / len(recent_requests),
            "success_rate": successful / len(recent_requests),
            "throughput": len(recent_requests) / time_window,
        }
    
    async def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get metrics for a specific agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dict[str, Any]: Agent-specific metrics
        """
        if agent_id not in self.agent_metrics:
            return {"error": "Agent not found"}
        
        agent_requests = list(self.agent_metrics[agent_id])
        
        if not agent_requests:
            return {
                "agent_id": agent_id,
                "total_requests": 0,
                "avg_processing_time": 0.0,
                "success_rate": 0.0,
                "avg_confidence": 0.0,
            }
        
        total_time = sum(req["processing_time"] for req in agent_requests)
        successful = sum(1 for req in agent_requests if req["success"])
        total_confidence = sum(req["confidence"] for req in agent_requests)
        
        return {
            "agent_id": agent_id,
            "total_requests": len(agent_requests),
            "avg_processing_time": total_time / len(agent_requests),
            "success_rate": successful / len(agent_requests),
            "avg_confidence": total_confidence / len(agent_requests),
            "last_request_time": agent_requests[-1]["timestamp"],
        }
    
    async def _check_alerts(self, processing_time: float, success: bool) -> None:
        """
        Check if any alert thresholds have been exceeded.
        
        Args:
            processing_time: Processing time for the request
            success: Whether the request was successful
        """
        # Check response time threshold
        response_time_threshold = self.alert_thresholds.get("response_time", 5.0)
        if processing_time > response_time_threshold:
            self.logger.warning(
                f"Response time alert: {processing_time:.3f}s exceeds threshold {response_time_threshold}s"
            )
        
        # Check error rate threshold
        if not success:
            error_rate_threshold = self.alert_thresholds.get("error_rate", 0.1)
            current_error_rate = self.failed_requests / self.total_requests
            if current_error_rate > error_rate_threshold:
                self.logger.warning(
                    f"Error rate alert: {current_error_rate:.3f} exceeds threshold {error_rate_threshold}"
                )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of performance metrics.
        
        Returns:
            Dict[str, Any]: Performance summary
        """
        if self.total_requests == 0:
            return {
                "status": "no_data",
                "message": "No requests processed yet"
            }
        
        avg_processing_time = self.total_processing_time / self.total_requests
        success_rate = self.successful_requests / self.total_requests
        
        # Determine performance status
        if success_rate >= 0.95 and avg_processing_time <= 1.0:
            status = "excellent"
        elif success_rate >= 0.90 and avg_processing_time <= 2.0:
            status = "good"
        elif success_rate >= 0.80 and avg_processing_time <= 5.0:
            status = "fair"
        else:
            status = "poor"
        
        return {
            "status": status,
            "total_requests": self.total_requests,
            "success_rate": success_rate,
            "avg_processing_time": avg_processing_time,
            "active_agents": len(self.agent_metrics),
        }

