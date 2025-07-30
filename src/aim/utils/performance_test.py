"""
Performance testing and benchmarking for the AIM Framework.

This module provides comprehensive performance testing capabilities
including load testing, stress testing, and benchmark analysis.
"""

import asyncio
import aiohttp
import time
import statistics
import json
import argparse
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Individual test result."""
    timestamp: datetime
    response_time: float
    status_code: int
    success: bool
    error: Optional[str] = None


@dataclass
class BenchmarkResults:
    """Comprehensive benchmark results."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    requests_per_second: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    errors: Dict[str, int]


class PerformanceTester:
    """Performance testing framework for the AIM Framework API."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[TestResult] = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, 
                          endpoint: str, 
                          method: str = "GET", 
                          data: Optional[Dict] = None,
                          headers: Optional[Dict] = None) -> TestResult:
        """Test a single endpoint and record the result."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                headers=headers
            ) as response:
                await response.text()  # Ensure response is fully read
                response_time = time.time() - start_time
                
                return TestResult(
                    timestamp=datetime.now(),
                    response_time=response_time,
                    status_code=response.status,
                    success=200 <= response.status < 400
                )
        
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                timestamp=datetime.now(),
                response_time=response_time,
                status_code=0,
                success=False,
                error=str(e)
            )
    
    async def load_test(self,
                       endpoint: str,
                       concurrent_users: int = 10,
                       requests_per_user: int = 100,
                       method: str = "GET",
                       data: Optional[Dict] = None,
                       headers: Optional[Dict] = None) -> BenchmarkResults:
        """Perform load testing on an endpoint."""
        logger.info(f"Starting load test: {concurrent_users} users, {requests_per_user} requests each")
        
        async def user_session():
            """Simulate a single user session."""
            user_results = []
            for _ in range(requests_per_user):
                result = await self.test_endpoint(endpoint, method, data, headers)
                user_results.append(result)
                # Small delay between requests
                await asyncio.sleep(0.01)
            return user_results
        
        # Run concurrent user sessions
        start_time = time.time()
        tasks = [user_session() for _ in range(concurrent_users)]
        all_results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Flatten results
        self.results = [result for user_results in all_results for result in user_results]
        
        return self._calculate_benchmark_results(total_time)
    
    async def stress_test(self,
                         endpoint: str,
                         max_concurrent_users: int = 100,
                         ramp_up_time: int = 60,
                         test_duration: int = 300,
                         method: str = "GET",
                         data: Optional[Dict] = None,
                         headers: Optional[Dict] = None) -> Dict[int, BenchmarkResults]:
        """Perform stress testing with gradually increasing load."""
        logger.info(f"Starting stress test: ramping up to {max_concurrent_users} users over {ramp_up_time}s")
        
        results_by_load = {}
        step_size = max(1, max_concurrent_users // 10)
        
        for concurrent_users in range(step_size, max_concurrent_users + 1, step_size):
            logger.info(f"Testing with {concurrent_users} concurrent users")
            
            # Calculate requests per user based on test duration
            requests_per_user = max(1, test_duration // 10)
            
            benchmark = await self.load_test(
                endpoint=endpoint,
                concurrent_users=concurrent_users,
                requests_per_user=requests_per_user,
                method=method,
                data=data,
                headers=headers
            )
            
            results_by_load[concurrent_users] = benchmark
            
            # Break if error rate is too high
            if benchmark.error_rate > 50:
                logger.warning(f"High error rate ({benchmark.error_rate:.1f}%) at {concurrent_users} users")
                break
            
            # Small delay between load levels
            await asyncio.sleep(5)
        
        return results_by_load
    
    async def benchmark_all_endpoints(self) -> Dict[str, BenchmarkResults]:
        """Benchmark all major API endpoints."""
        endpoints = [
            ("/health", "GET", None),
            ("/agents", "GET", None),
            ("/process", "POST", {"message": "test message", "agent_id": "test"}),
            ("/context", "POST", {"user_id": "test_user"}),
            ("/metrics", "GET", None)
        ]
        
        results = {}
        
        for endpoint, method, data in endpoints:
            logger.info(f"Benchmarking {method} {endpoint}")
            try:
                benchmark = await self.load_test(
                    endpoint=endpoint,
                    concurrent_users=5,
                    requests_per_user=20,
                    method=method,
                    data=data
                )
                results[f"{method} {endpoint}"] = benchmark
            except Exception as e:
                logger.error(f"Failed to benchmark {endpoint}: {e}")
        
        return results
    
    def _calculate_benchmark_results(self, total_time: float) -> BenchmarkResults:
        """Calculate comprehensive benchmark statistics."""
        if not self.results:
            raise ValueError("No test results available")
        
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        response_times = [r.response_time for r in successful_results]
        
        # Count errors by type
        errors = {}
        for result in failed_results:
            error_key = f"HTTP {result.status_code}" if result.status_code > 0 else "Network Error"
            errors[error_key] = errors.get(error_key, 0) + 1
        
        return BenchmarkResults(
            total_requests=len(self.results),
            successful_requests=len(successful_results),
            failed_requests=len(failed_results),
            total_time=total_time,
            requests_per_second=len(self.results) / total_time if total_time > 0 else 0,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            median_response_time=statistics.median(response_times) if response_times else 0,
            p95_response_time=self._percentile(response_times, 95) if response_times else 0,
            p99_response_time=self._percentile(response_times, 99) if response_times else 0,
            error_rate=(len(failed_results) / len(self.results)) * 100,
            errors=errors
        )
    
    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def generate_report(self, results: BenchmarkResults, output_file: Optional[str] = None) -> str:
        """Generate a detailed performance report."""
        report = f"""
AIM Framework Performance Test Report
=====================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary
-------
Total Requests: {results.total_requests:,}
Successful Requests: {results.successful_requests:,}
Failed Requests: {results.failed_requests:,}
Error Rate: {results.error_rate:.2f}%
Total Time: {results.total_time:.2f}s
Requests/Second: {results.requests_per_second:.2f}

Response Times
--------------
Average: {results.avg_response_time*1000:.2f}ms
Minimum: {results.min_response_time*1000:.2f}ms
Maximum: {results.max_response_time*1000:.2f}ms
Median: {results.median_response_time*1000:.2f}ms
95th Percentile: {results.p95_response_time*1000:.2f}ms
99th Percentile: {results.p99_response_time*1000:.2f}ms

Errors
------
"""
        
        if results.errors:
            for error_type, count in results.errors.items():
                report += f"{error_type}: {count:,} ({count/results.total_requests*100:.2f}%)\n"
        else:
            report += "No errors detected\n"
        
        # Performance assessment
        report += "\nPerformance Assessment\n"
        report += "----------------------\n"
        
        if results.error_rate < 1:
            report += "✓ Error rate is excellent (< 1%)\n"
        elif results.error_rate < 5:
            report += "⚠ Error rate is acceptable (< 5%)\n"
        else:
            report += "✗ Error rate is high (>= 5%)\n"
        
        if results.avg_response_time < 0.1:
            report += "✓ Average response time is excellent (< 100ms)\n"
        elif results.avg_response_time < 0.5:
            report += "⚠ Average response time is acceptable (< 500ms)\n"
        else:
            report += "✗ Average response time is slow (>= 500ms)\n"
        
        if results.requests_per_second > 100:
            report += "✓ Throughput is excellent (> 100 req/s)\n"
        elif results.requests_per_second > 50:
            report += "⚠ Throughput is acceptable (> 50 req/s)\n"
        else:
            report += "✗ Throughput is low (<= 50 req/s)\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to {output_file}")
        
        return report


async def run_performance_tests(base_url: str = "http://localhost:5000"):
    """Run comprehensive performance tests."""
    async with PerformanceTester(base_url) as tester:
        print("Starting AIM Framework Performance Tests...")
        
        # Test 1: Health endpoint load test
        print("\n1. Health Endpoint Load Test")
        health_results = await tester.load_test(
            endpoint="/health",
            concurrent_users=10,
            requests_per_user=50
        )
        print(f"Health endpoint: {health_results.requests_per_second:.2f} req/s, "
              f"{health_results.avg_response_time*1000:.2f}ms avg")
        
        # Test 2: Process endpoint load test
        print("\n2. Process Endpoint Load Test")
        process_results = await tester.load_test(
            endpoint="/process",
            method="POST",
            data={"message": "performance test", "agent_id": "test"},
            concurrent_users=5,
            requests_per_user=20
        )
        print(f"Process endpoint: {process_results.requests_per_second:.2f} req/s, "
              f"{process_results.avg_response_time*1000:.2f}ms avg")
        
        # Test 3: Stress test
        print("\n3. Stress Test")
        stress_results = await tester.stress_test(
            endpoint="/health",
            max_concurrent_users=50,
            test_duration=60
        )
        
        print("\nStress Test Results:")
        for users, results in stress_results.items():
            print(f"  {users} users: {results.requests_per_second:.2f} req/s, "
                  f"{results.error_rate:.1f}% errors")
        
        # Generate comprehensive report
        print("\n4. Generating Report")
        report = tester.generate_report(health_results, "performance_report.txt")
        print("Performance test completed!")
        
        return {
            "health": health_results,
            "process": process_results,
            "stress": stress_results
        }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="AIM Framework Performance Testing")
    parser.add_argument("--url", default="http://localhost:5000", 
                       help="Base URL of the AIM Framework API")
    parser.add_argument("--endpoint", default="/health",
                       help="Specific endpoint to test")
    parser.add_argument("--users", type=int, default=10,
                       help="Number of concurrent users")
    parser.add_argument("--requests", type=int, default=100,
                       help="Number of requests per user")
    parser.add_argument("--method", default="GET",
                       help="HTTP method to use")
    parser.add_argument("--data", type=str,
                       help="JSON data to send (for POST requests)")
    parser.add_argument("--output", type=str,
                       help="Output file for the report")
    
    args = parser.parse_args()
    
    async def run_test():
        data = json.loads(args.data) if args.data else None
        
        async with PerformanceTester(args.url) as tester:
            results = await tester.load_test(
                endpoint=args.endpoint,
                concurrent_users=args.users,
                requests_per_user=args.requests,
                method=args.method,
                data=data
            )
            
            report = tester.generate_report(results, args.output)
            print(report)
            
            return results
    
    return asyncio.run(run_test())


if __name__ == "__main__":
    main()