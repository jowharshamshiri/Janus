#!/usr/bin/env python3
"""
Cross-Platform Performance Benchmark Suite for Janus
Measures latency, throughput, and concurrent performance across all implementations
"""

import json
import socket
import os
import time
import subprocess
import threading
import statistics
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import logging

@dataclass
class BenchmarkResult:
    """Individual benchmark result"""
    name: str
    implementation: str
    metric: str
    value: float
    unit: str
    details: Dict[str, Any] = None

class PerformanceBenchmark:
    """Performance benchmark suite for Janus implementations"""
    
    def __init__(self, config_path: str = "test-manifest.json", verbose: bool = False):
        self.config_path = config_path
        self.verbose = verbose
        self.config = self._load_config()
        self.results: List[BenchmarkResult] = []
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("PerformanceBenchmark")
    
    def _load_config(self) -> Dict:
        """Load benchmark configuration"""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def start_server(self, impl_name: str, socket_path: str) -> Optional[subprocess.Popen]:
        """Start server implementation"""
        impl = self.config["implementations"][impl_name]
        self.logger.info(f"Starting {impl_name} server for benchmarking")
        
        # Clean up existing socket
        try:
            os.unlink(socket_path)
        except FileNotFoundError:
            pass
        
        try:
            # Build server request using unified_binary and listen_args
            if impl_name == "rust":
                cmd = ["cargo", "run", "--bin", "janus", "--"] + impl["listen_args"]
            elif impl_name == "swift": 
                cmd = ["swift", "run", "SwiftJanusDgram"] + impl["listen_args"]
            else:
                cmd = [impl["unified_binary"]] + impl["listen_args"]
                
            proc = subprocess.Popen(
                cmd,
                cwd=impl["directory"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for server to start
            max_wait = 10
            for _ in range(max_wait * 10):
                if os.path.exists(socket_path):
                    return proc
                if proc.poll() is not None:
                    return None
                time.sleep(0.1)
            
            # Timeout
            proc.terminate()
            return None
            
        except Exception as e:
            self.logger.error(f"Error starting {impl_name} server: {e}")
            return None
    
    def send_message(self, socket_path: str, message: Dict) -> Tuple[bool, float, Optional[Dict]]:
        """Send a single message and measure response time"""
        start_time = time.perf_counter()
        
        try:
            # Create client socket
            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            reply_path = f"/tmp/bench_reply_{threading.get_ident()}_{int(time.time() * 1000000)}.sock"
            
            try:
                # Bind reply socket
                client_sock.bind(reply_path)
                message['reply_to'] = reply_path
                
                # Send message
                message_json = json.dumps(message).encode('utf-8')
                send_time = time.perf_counter()
                client_sock.sendto(message_json, socket_path)
                
                # Wait for response
                client_sock.settimeout(5.0)
                response_data, _ = client_sock.recvfrom(4096)
                receive_time = time.perf_counter()
                
                # Parse response
                response = json.loads(response_data.decode('utf-8'))
                
                latency = receive_time - send_time
                return True, latency, response
                
            finally:
                client_sock.close()
                try:
                    os.unlink(reply_path)
                except FileNotFoundError:
                    pass
                    
        except Exception as e:
            end_time = time.perf_counter()
            self.logger.debug(f"Message send failed: {e}")
            return False, end_time - start_time, None
    
    def latency_benchmark(self, impl_name: str, socket_path: str, iterations: int = 1000) -> BenchmarkResult:
        """Measure request-response latency"""
        self.logger.info(f"Running latency benchmark for {impl_name} ({iterations} iterations)")
        
        message = {
            'channel': 'system',
            'request': 'ping',
            'parameters': {'message': 'benchmark'}
        }
        
        latencies = []
        failures = 0
        
        for i in range(iterations):
            success, latency, response = self.send_message(socket_path, message.copy())
            
            if success and response and response.get('status') == 'success':
                latencies.append(latency * 1000)  # Convert to milliseconds
            else:
                failures += 1
            
            if i % 100 == 0 and i > 0:
                self.logger.debug(f"Completed {i}/{iterations} latency tests")
        
        if not latencies:
            return BenchmarkResult(
                name="latency",
                implementation=impl_name,
                metric="error",
                value=100.0,
                unit="percent",
                details={"error": "All requests failed", "failures": failures}
            )
        
        # Calculate statistics
        avg_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        
        self.logger.info(f"✅ {impl_name} latency: avg={avg_latency:.2f}ms, p95={p95_latency:.2f}ms, p99={p99_latency:.2f}ms")
        
        return BenchmarkResult(
            name="latency",
            implementation=impl_name,
            metric="avg_latency_ms",
            value=avg_latency,
            unit="milliseconds",
            details={
                "median_ms": median_latency,
                "p95_ms": p95_latency,
                "p99_ms": p99_latency,
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "stddev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "success_rate": (iterations - failures) / iterations,
                "total_requests": iterations,
                "failures": failures
            }
        )
    
    def throughput_benchmark(self, impl_name: str, socket_path: str, 
                           duration_seconds: int = 30, 
                           concurrent_clients: int = 10) -> BenchmarkResult:
        """Measure message throughput"""
        self.logger.info(f"Running throughput benchmark for {impl_name} "
                        f"({duration_seconds}s, {concurrent_clients} clients)")
        
        message = {
            'channel': 'system',
            'request': 'echo',
            'parameters': {'data': 'throughput_test_data'}
        }
        
        total_requests = 0
        total_failures = 0
        start_time = time.perf_counter()
        end_time = start_time + duration_seconds
        
        def client_worker():
            requests = 0
            failures = 0
            
            while time.perf_counter() < end_time:
                success, latency, response = self.send_message(socket_path, message.copy())
                requests += 1
                
                if not success or not response or response.get('status') != 'success':
                    failures += 1
                
                # Small delay to prevent overwhelming
                time.sleep(0.001)
            
            return requests, failures
        
        # Run concurrent clients
        with ThreadPoolExecutor(max_workers=concurrent_clients) as executor:
            futures = [executor.submit(client_worker) for _ in range(concurrent_clients)]
            
            for future in as_completed(futures):
                try:
                    requests, failures = future.result()
                    total_requests += requests
                    total_failures += failures
                except Exception as e:
                    self.logger.error(f"Client worker failed: {e}")
                    total_failures += 1
        
        actual_duration = time.perf_counter() - start_time
        requests_per_second = total_requests / actual_duration if actual_duration > 0 else 0
        success_rate = (total_requests - total_failures) / total_requests if total_requests > 0 else 0
        
        self.logger.info(f"✅ {impl_name} throughput: {requests_per_second:.1f} req/s "
                        f"({success_rate:.1%} success rate)")
        
        return BenchmarkResult(
            name="throughput",
            implementation=impl_name,
            metric="requests_per_second",
            value=requests_per_second,
            unit="req/s",
            details={
                "total_requests": total_requests,
                "total_failures": total_failures,
                "success_rate": success_rate,
                "duration_seconds": actual_duration,
                "concurrent_clients": concurrent_clients
            }
        )
    
    def concurrent_benchmark(self, impl_name: str, socket_path: str,
                           concurrent_clients: int = 50,
                           requests_per_client: int = 100) -> BenchmarkResult:
        """Measure concurrent client handling"""
        self.logger.info(f"Running concurrency benchmark for {impl_name} "
                        f"({concurrent_clients} clients, {requests_per_client} req/client)")
        
        message = {
            'channel': 'system',
            'request': 'ping',
            'parameters': {'message': f'concurrent_test'}
        }
        
        def client_worker(client_id: int):
            requests = 0
            failures = 0
            latencies = []
            
            for i in range(requests_per_client):
                success, latency, response = self.send_message(socket_path, message.copy())
                requests += 1
                
                if success and response and response.get('status') == 'success':
                    latencies.append(latency * 1000)  # Convert to ms
                else:
                    failures += 1
            
            return {
                'client_id': client_id,
                'requests': requests,
                'failures': failures,
                'latencies': latencies,
                'avg_latency': statistics.mean(latencies) if latencies else 0
            }
        
        start_time = time.perf_counter()
        
        # Run concurrent clients
        with ThreadPoolExecutor(max_workers=concurrent_clients) as executor:
            futures = [executor.submit(client_worker, i) for i in range(concurrent_clients)]
            client_results = []
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    client_results.append(result)
                except Exception as e:
                    self.logger.error(f"Concurrent client failed: {e}")
        
        end_time = time.perf_counter()
        
        # Aggregate results
        total_requests = sum(r['requests'] for r in client_results)
        total_failures = sum(r['failures'] for r in client_results)
        all_latencies = []
        for r in client_results:
            all_latencies.extend(r['latencies'])
        
        success_rate = (total_requests - total_failures) / total_requests if total_requests > 0 else 0
        avg_latency = statistics.mean(all_latencies) if all_latencies else 0
        duration = end_time - start_time
        
        self.logger.info(f"✅ {impl_name} concurrency: {success_rate:.1%} success rate, "
                        f"avg latency {avg_latency:.2f}ms")
        
        return BenchmarkResult(
            name="concurrency",
            implementation=impl_name,
            metric="success_rate",
            value=success_rate,
            unit="percent",
            details={
                "total_requests": total_requests,
                "total_failures": total_failures,
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) > 20 else 0,
                "duration_seconds": duration,
                "concurrent_clients": concurrent_clients,
                "requests_per_client": requests_per_client,
                "client_results": len(client_results)
            }
        )
    
    def memory_benchmark(self, impl_name: str, socket_path: str, duration_seconds: int = 60) -> BenchmarkResult:
        """Measure memory usage during operation"""
        self.logger.info(f"Running memory benchmark for {impl_name} ({duration_seconds}s)")
        
        # Find server process
        impl = self.config["implementations"][impl_name]
        try:
            # Get server process info
            result = subprocess.run(
                ['pgrep', '-f', impl["server_request"][0]],
                capture_output=True, text=True
            )
            
            if not result.stdout:
                return BenchmarkResult(
                    name="memory",
                    implementation=impl_name,
                    metric="error",
                    value=0,
                    unit="bytes",
                    details={"error": "Server process not found"}
                )
            
            pid = int(result.stdout.strip().split('\n')[0])
            
            # Monitor memory usage
            memory_samples = []
            start_time = time.time()
            
            # Send continuous load while monitoring
            def load_generator():
                message = {
                    'channel': 'system',
                    'request': 'ping',
                    'parameters': {'message': 'memory_test'}
                }
                
                while time.time() - start_time < duration_seconds:
                    self.send_message(socket_path, message.copy())
                    time.sleep(0.01)  # 100 req/s
            
            load_thread = threading.Thread(target=load_generator)
            load_thread.start()
            
            # Sample memory usage
            while time.time() - start_time < duration_seconds:
                try:
                    result = subprocess.run(
                        ['ps', '-p', str(pid), '-o', 'rss='],
                        capture_output=True, text=True, timeout=1
                    )
                    
                    if result.stdout:
                        memory_kb = int(result.stdout.strip())
                        memory_samples.append(memory_kb * 1024)  # Convert to bytes
                
                except (ValueError, subprocess.TimeoutExpired):
                    pass
                
                time.sleep(1)  # Sample every second
            
            load_thread.join()
            
            if not memory_samples:
                return BenchmarkResult(
                    name="memory",
                    implementation=impl_name,
                    metric="error",
                    value=0,
                    unit="bytes",
                    details={"error": "No memory samples collected"}
                )
            
            avg_memory = statistics.mean(memory_samples)
            max_memory = max(memory_samples)
            min_memory = min(memory_samples)
            
            self.logger.info(f"✅ {impl_name} memory: avg={avg_memory/1024/1024:.1f}MB, "
                           f"max={max_memory/1024/1024:.1f}MB")
            
            return BenchmarkResult(
                name="memory",
                implementation=impl_name,
                metric="avg_memory_bytes",
                value=avg_memory,
                unit="bytes",
                details={
                    "max_memory_bytes": max_memory,
                    "min_memory_bytes": min_memory,
                    "avg_memory_mb": avg_memory / 1024 / 1024,
                    "max_memory_mb": max_memory / 1024 / 1024,
                    "samples": len(memory_samples),
                    "duration_seconds": duration_seconds
                }
            )
            
        except Exception as e:
            return BenchmarkResult(
                name="memory",
                implementation=impl_name,
                metric="error",
                value=0,
                unit="bytes",
                details={"error": str(e)}
            )
    
    def benchmark_implementation(self, impl_name: str) -> List[BenchmarkResult]:
        """Run all benchmarks for an implementation"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"BENCHMARKING {impl_name.upper()}")
        self.logger.info(f"{'='*60}")
        
        socket_path = f"/tmp/benchmark_{impl_name}.sock"
        results = []
        
        # Start server
        server_proc = self.start_server(impl_name, socket_path)
        if not server_proc:
            self.logger.error(f"Failed to start {impl_name} server")
            return [BenchmarkResult(
                name="server_start",
                implementation=impl_name,
                metric="error",
                value=0,
                unit="none",
                details={"error": "Server failed to start"}
            )]
        
        try:
            # Run benchmarks
            benchmarks = self.config.get("performance_benchmarks", {})
            
            # Latency test
            if "latency_test" in benchmarks:
                config = benchmarks["latency_test"]
                result = self.latency_benchmark(
                    impl_name, socket_path, 
                    config.get("iterations", 1000)
                )
                results.append(result)
            
            # Throughput test
            if "throughput_test" in benchmarks:
                config = benchmarks["throughput_test"]
                result = self.throughput_benchmark(
                    impl_name, socket_path,
                    config.get("duration_seconds", 30),
                    config.get("concurrent_clients", 10)
                )
                results.append(result)
            
            # Concurrency test
            if "concurrent_test" in benchmarks:
                config = benchmarks["concurrent_test"]
                result = self.concurrent_benchmark(
                    impl_name, socket_path,
                    config.get("concurrent_clients", 50),
                    config.get("requests_per_client", 100)
                )
                results.append(result)
            
            # Memory test
            result = self.memory_benchmark(impl_name, socket_path, 30)
            results.append(result)
            
        finally:
            # Cleanup
            try:
                server_proc.terminate()
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()
            except Exception as e:
                self.logger.warning(f"Error stopping server: {e}")
            
            try:
                os.unlink(socket_path)
            except FileNotFoundError:
                pass
        
        return results
    
    def generate_report(self, all_results: List[BenchmarkResult]) -> str:
        """Generate comprehensive benchmark report"""
        # Group results by benchmark type
        by_benchmark = {}
        for result in all_results:
            if result.name not in by_benchmark:
                by_benchmark[result.name] = []
            by_benchmark[result.name].append(result)
        
        report = []
        report.append("=" * 80)
        report.append("JANUS CROSS-PLATFORM PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
        report.append("")
        
        # Summary table
        implementations = list(set(r.implementation for r in all_results))
        
        for benchmark_name, results in by_benchmark.items():
            if benchmark_name == "server_start":
                continue
                
            report.append(f"{benchmark_name.upper()} BENCHMARK")
            report.append("-" * 40)
            
            for result in results:
                if result.metric == "error":
                    report.append(f"{result.implementation:12} ERROR: {result.details.get('error', 'Unknown error')}")
                else:
                    report.append(f"{result.implementation:12} {result.value:8.2f} {result.unit}")
                    
                    # Add key details
                    if result.details:
                        for key, value in result.details.items():
                            if key in ['p95_ms', 'p99_ms', 'success_rate', 'max_memory_mb']:
                                report.append(f"{'':14} {key}: {value}")
            
            report.append("")
        
        # Performance comparison
        report.append("PERFORMANCE COMPARISON")
        report.append("-" * 40)
        
        # Find best performer for each metric
        for benchmark_name, results in by_benchmark.items():
            if benchmark_name == "server_start":
                continue
                
            valid_results = [r for r in results if r.metric != "error"]
            if not valid_results:
                continue
            
            if benchmark_name == "latency":
                best = min(valid_results, key=lambda x: x.value)
                report.append(f"Lowest Latency:    {best.implementation} ({best.value:.2f}ms)")
            elif benchmark_name == "throughput":
                best = max(valid_results, key=lambda x: x.value)
                report.append(f"Highest Throughput: {best.implementation} ({best.value:.1f} req/s)")
            elif benchmark_name == "concurrency":
                best = max(valid_results, key=lambda x: x.value)
                report.append(f"Best Concurrency:   {best.implementation} ({best.value:.1%} success)")
            elif benchmark_name == "memory":
                best = min(valid_results, key=lambda x: x.value)
                report.append(f"Lowest Memory:      {best.implementation} ({best.value/1024/1024:.1f}MB)")
        
        return "\n".join(report)
    
    def run_all_benchmarks(self, implementations: List[str] = None) -> List[BenchmarkResult]:
        """Run benchmarks for all implementations"""
        if implementations is None:
            implementations = list(self.config["implementations"].keys())
        
        all_results = []
        
        for impl_name in implementations:
            results = self.benchmark_implementation(impl_name)
            all_results.extend(results)
            self.results.extend(results)
        
        return all_results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance benchmark suite")
    parser.add_argument("--config", default="test-manifest.json", help="Test configuration file")
    parser.add_argument("--implementations", nargs="+", 
                       help="Implementations to benchmark (default: all)")
    parser.add_argument("--output", default="benchmark_results.json", help="Results output file")
    parser.add_argument("--report", default="benchmark_report.txt", help="Report output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark(args.config, args.verbose)
    results = benchmark.run_all_benchmarks(args.implementations)
    
    # Write detailed results
    results_data = [
        {
            'name': r.name,
            'implementation': r.implementation,
            'metric': r.metric,
            'value': r.value,
            'unit': r.unit,
            'details': r.details
        }
        for r in results
    ]
    
    with open(args.output, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    # Generate report
    report = benchmark.generate_report(results)
    
    with open(args.report, 'w') as f:
        f.write(report)
    
    print(report)
    print(f"\nDetailed results: {args.output}")
    print(f"Report file: {args.report}")

if __name__ == "__main__":
    main()