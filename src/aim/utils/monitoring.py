"""
Monitoring and metrics collection for the AIM Framework.

This module provides comprehensive monitoring capabilities including
health checks, performance metrics, and system monitoring.
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status information."""
    status: str
    timestamp: datetime
    uptime: float
    version: str
    details: Dict[str, Any]


@dataclass
class PerformanceMetrics:
    """Performance metrics data."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    request_count: int
    response_time_avg: float
    error_rate: float
    active_connections: int


class MetricsCollector:
    """Collects and manages system and application metrics."""
    
    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.metrics_history: List[PerformanceMetrics] = []
        self.request_times: List[float] = []
        self.error_count = 0
        self.request_count = 0
        self.start_time = time.time()
        self.active_connections = 0
        self._collecting = False
        self._collection_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start_collection(self):
        """Start metrics collection in background thread."""
        if self._collecting:
            return
        
        self._collecting = True
        self._collection_thread = threading.Thread(
            target=self._collect_metrics_loop,
            daemon=True
        )
        self._collection_thread.start()
        logger.info("Metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection."""
        self._collecting = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        logger.info("Metrics collection stopped")
    
    def _collect_metrics_loop(self):
        """Main metrics collection loop."""
        while self._collecting:
            try:
                metrics = self._collect_current_metrics()
                with self._lock:
                    self.metrics_history.append(metrics)
                    # Keep only last 1000 metrics (configurable)
                    if len(self.metrics_history) > 1000:
                        self.metrics_history = self.metrics_history[-1000:]
                
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_current_metrics(self) -> PerformanceMetrics:
        """Collect current system metrics."""
        # CPU and memory usage
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv,
            'packets_sent': network.packets_sent,
            'packets_recv': network.packets_recv
        }
        
        # Application metrics
        with self._lock:
            avg_response_time = (
                sum(self.request_times) / len(self.request_times)
                if self.request_times else 0.0
            )
            error_rate = (
                self.error_count / max(self.request_count, 1) * 100
            )
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            network_io=network_io,
            request_count=self.request_count,
            response_time_avg=avg_response_time,
            error_rate=error_rate,
            active_connections=self.active_connections
        )
    
    def record_request(self, response_time: float, is_error: bool = False):
        """Record a request for metrics."""
        with self._lock:
            self.request_count += 1
            self.request_times.append(response_time)
            
            # Keep only last 1000 request times
            if len(self.request_times) > 1000:
                self.request_times = self.request_times[-1000:]
            
            if is_error:
                self.error_count += 1
    
    def increment_connections(self):
        """Increment active connections counter."""
        with self._lock:
            self.active_connections += 1
    
    def decrement_connections(self):
        """Decrement active connections counter."""
        with self._lock:
            self.active_connections = max(0, self.active_connections - 1)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics as dictionary."""
        metrics = self._collect_current_metrics()
        return asdict(metrics)
    
    def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get metrics history for specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            filtered_metrics = [
                asdict(m) for m in self.metrics_history
                if m.timestamp >= cutoff_time
            ]
        
        return filtered_metrics


class HealthChecker:
    """Performs health checks on the system and application."""
    
    def __init__(self, framework_version: str = "1.0.0"):
        self.framework_version = framework_version
        self.start_time = time.time()
        self.health_checks: Dict[str, callable] = {}
    
    def register_health_check(self, name: str, check_func: callable):
        """Register a custom health check function."""
        self.health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    def get_health_status(self) -> HealthStatus:
        """Get comprehensive health status."""
        uptime = time.time() - self.start_time
        
        # Basic system checks
        details = {
            "system": self._check_system_health(),
            "application": self._check_application_health(),
            "custom": self._run_custom_checks()
        }
        
        # Determine overall status
        status = "healthy"
        for category, checks in details.items():
            for check_name, check_result in checks.items():
                if not check_result.get("healthy", True):
                    status = "unhealthy"
                    break
            if status == "unhealthy":
                break
        
        return HealthStatus(
            status=status,
            timestamp=datetime.now(),
            uptime=uptime,
            version=self.framework_version,
            details=details
        )
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check system-level health."""
        checks = {}
        
        # CPU usage check
        cpu_usage = psutil.cpu_percent(interval=1)
        checks["cpu"] = {
            "healthy": cpu_usage < 90,
            "value": cpu_usage,
            "unit": "percent",
            "threshold": 90
        }
        
        # Memory usage check
        memory = psutil.virtual_memory()
        checks["memory"] = {
            "healthy": memory.percent < 90,
            "value": memory.percent,
            "unit": "percent",
            "threshold": 90,
            "available": memory.available
        }
        
        # Disk usage check
        disk = psutil.disk_usage('/')
        checks["disk"] = {
            "healthy": disk.percent < 90,
            "value": disk.percent,
            "unit": "percent",
            "threshold": 90,
            "free": disk.free
        }
        
        return checks
    
    def _check_application_health(self) -> Dict[str, Any]:
        """Check application-level health."""
        checks = {}
        
        # Framework status
        checks["framework"] = {
            "healthy": True,
            "status": "running",
            "uptime": time.time() - self.start_time
        }
        
        # Add more application-specific checks here
        
        return checks
    
    def _run_custom_checks(self) -> Dict[str, Any]:
        """Run custom registered health checks."""
        results = {}
        
        for name, check_func in self.health_checks.items():
            try:
                result = check_func()
                results[name] = result if isinstance(result, dict) else {"healthy": bool(result)}
            except Exception as e:
                logger.error(f"Health check '{name}' failed: {e}")
                results[name] = {
                    "healthy": False,
                    "error": str(e)
                }
        
        return results


class Monitor:
    """Main monitoring class that coordinates metrics and health checks."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_collector = MetricsCollector(
            collection_interval=config.get("collection_interval", 30)
        )
        self.health_checker = HealthChecker(
            framework_version=config.get("framework_version", "1.0.0")
        )
        self.enabled = config.get("enabled", True)
    
    def start(self):
        """Start monitoring services."""
        if not self.enabled:
            logger.info("Monitoring is disabled")
            return
        
        self.metrics_collector.start_collection()
        logger.info("Monitoring started")
    
    def stop(self):
        """Stop monitoring services."""
        self.metrics_collector.stop_collection()
        logger.info("Monitoring stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status."""
        health_status = self.health_checker.get_health_status()
        current_metrics = self.metrics_collector.get_current_metrics()
        
        return {
            "health": asdict(health_status),
            "metrics": current_metrics,
            "monitoring": {
                "enabled": self.enabled,
                "collection_interval": self.metrics_collector.collection_interval
            }
        }
    
    def record_request(self, response_time: float, is_error: bool = False):
        """Record a request for monitoring."""
        self.metrics_collector.record_request(response_time, is_error)
    
    def register_health_check(self, name: str, check_func: callable):
        """Register a custom health check."""
        self.health_checker.register_health_check(name, check_func)