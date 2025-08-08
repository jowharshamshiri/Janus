#!/usr/bin/env python3
"""
Simple Cross-Platform Performance Benchmark for Janus
Measures latency and throughput across Go, Rust, Swift implementations
"""

import json
import socket
import os
import time
import subprocess
import threading
import statistics
import signal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class BenchmarkResult:
    """Benchmark result data class"""
    implementation: str
    metric: str
    value: float
    unit: str
    details: Dict = None

class SimpleBenchmark:
    """Simple benchmark runner for Janus implementations"""
    
    def __init__(self):
        self.results = []
        
    def run_server(self, impl_name: str, binary_path: str, socket_path: str, timeout: int = 60) -> Optional[subprocess.Popen]:
        """Start a server process"""
        print(f"Starting {impl_name} server...")
        
        # Clean up existing socket
        try:
            os.unlink(socket_path)
        except FileNotFoundError:
            pass
        
        try:
            cmd = [binary_path, "--listen", "--socket", socket_path]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for socket file to appear
            for _ in range(50):  # 5 second timeout
                if os.path.exists(socket_path):
                    time.sleep(0.2)  # Extra time for binding
                    return proc
                if proc.poll() is not None:
                    return None
                time.sleep(0.1)
            
            # Timeout - kill process
            proc.terminate()
            return None
            
        except Exception as e:
            print(f"Error starting {impl_name} server: {e}")
            return None
    
    def send_request(self, socket_path: str, request: str = "ping") -> Tuple[bool, float]:
        """Send a single request and measure latency"""
        start_time = time.perf_counter()
        
        try:
            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            reply_path = f"/tmp/bench_reply_{threading.get_ident()}_{int(time.time() * 1000000)}.sock"
            
            try:
                client_sock.bind(reply_path)
                
                message = {
                    'channel': 'system',
                    'request': request,
                    'parameters': {'message': 'benchmark'},
                    'reply_to': reply_path
                }
                
                message_data = json.dumps(message).encode('utf-8')
                send_time = time.perf_counter()
                client_sock.sendto(message_data, socket_path)
                
                client_sock.settimeout(2.0)
                response_data, _ = client_sock.recvfrom(4096)
                receive_time = time.perf_counter()
                
                response = json.loads(response_data.decode('utf-8'))
                latency = receive_time - send_time
                
                # Check if response is successful
                if response.get('status') in ['success', 'pong']:
                    return True, latency
                else:
                    return False, latency
                    
            finally:
                client_sock.close()
                try:
                    os.unlink(reply_path)
                except FileNotFoundError:
                    pass
                    
        except Exception as e:
            end_time = time.perf_counter()
            return False, end_time - start_time
    
    def latency_benchmark(self, impl_name: str, socket_path: str, iterations: int = 100) -> BenchmarkResult:
        """Measure request-response latency"""
        print(f"  Running latency test ({iterations} requests)...")
        
        latencies = []
        failures = 0
        
        for i in range(iterations):
            success, latency = self.send_request(socket_path)
            if success:
                latencies.append(latency * 1000)  # Convert to milliseconds
            else:
                failures += 1
        
        if not latencies:
            return BenchmarkResult(
                implementation=impl_name,
                metric="latency_error",
                value=100.0,
                unit="percent_failed",
                details={"failures": failures, "total": iterations}
            )
        
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        success_rate = len(latencies) / iterations
        
        return BenchmarkResult(
            implementation=impl_name,
            metric="latency",
            value=avg_latency,
            unit="milliseconds",
            details={
                "p95_ms": p95_latency,
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "success_rate": success_rate,
                "failures": failures
            }
        )
    
    def throughput_benchmark(self, impl_name: str, socket_path: str, duration: int = 10) -> BenchmarkResult:
        """Measure throughput over time"""
        print(f"  Running throughput test ({duration} seconds)...")
        
        start_time = time.perf_counter()
        end_time = start_time + duration
        successful_requests = 0
        total_requests = 0
        
        while time.perf_counter() < end_time:
            success, _ = self.send_request(socket_path)
            total_requests += 1
            if success:
                successful_requests += 1
        
        actual_duration = time.perf_counter() - start_time
        throughput = successful_requests / actual_duration
        
        return BenchmarkResult(
            implementation=impl_name,
            metric="throughput",
            value=throughput,
            unit="requests_per_second",
            details={
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "duration": actual_duration,
                "success_rate": successful_requests / total_requests if total_requests > 0 else 0
            }
        )
    
    def benchmark_implementation(self, impl_name: str, binary_path: str) -> List[BenchmarkResult]:
        """Run all benchmarks for one implementation"""
        print(f"\n{'='*50}")
        print(f"BENCHMARKING {impl_name.upper()}")
        print(f"{'='*50}")
        
        socket_path = f"/tmp/benchmark_{impl_name}.sock"
        results = []
        
        # Start server
        server_proc = self.run_server(impl_name, binary_path, socket_path)
        if not server_proc:
            print(f"❌ Failed to start {impl_name} server")
            return [BenchmarkResult(
                implementation=impl_name,
                metric="server_start",
                value=0,
                unit="boolean",
                details={"error": "Server failed to start"}
            )]
        
        try:
            # Latency test
            latency_result = self.latency_benchmark(impl_name, socket_path, 100)
            results.append(latency_result)
            
            if latency_result.metric != "latency_error":
                print(f"  ✅ Latency: {latency_result.value:.2f}ms avg, {latency_result.details['p95_ms']:.2f}ms p95")
            else:
                print(f"  ❌ Latency test failed: {latency_result.details['failures']}/{latency_result.details['total']} requests failed")
            
            # Throughput test
            throughput_result = self.throughput_benchmark(impl_name, socket_path, 10)
            results.append(throughput_result)
            
            print(f"  ✅ Throughput: {throughput_result.value:.1f} req/s ({throughput_result.details['success_rate']:.1%} success)")
            
        finally:
            # Cleanup server
            try:
                server_proc.terminate()
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()
            except Exception:
                pass
            
            try:
                os.unlink(socket_path)
            except FileNotFoundError:
                pass
        
        return results
    
    def generate_report(self, all_results: List[BenchmarkResult]) -> str:
        """Generate performance comparison report"""
        report = []
        report.append("=" * 70)
        report.append("JANUS CROSS-PLATFORM PERFORMANCE BENCHMARK RESULTS")
        report.append("=" * 70)
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
        report.append("")
        
        # Group by implementation
        by_impl = {}
        for result in all_results:
            if result.implementation not in by_impl:
                by_impl[result.implementation] = {}
            by_impl[result.implementation][result.metric] = result
        
        # Latency comparison
        report.append("LATENCY COMPARISON")
        report.append("-" * 30)
        latency_results = []
        for impl, metrics in by_impl.items():
            if 'latency' in metrics:
                result = metrics['latency']
                latency_results.append((impl, result.value, result.details['p95_ms']))
                report.append(f"{impl:10} {result.value:8.2f}ms avg  {result.details['p95_ms']:8.2f}ms p95")
            elif 'latency_error' in metrics:
                report.append(f"{impl:10} FAILED")
        
        # Throughput comparison
        report.append("")
        report.append("THROUGHPUT COMPARISON")
        report.append("-" * 30)
        throughput_results = []
        for impl, metrics in by_impl.items():
            if 'throughput' in metrics:
                result = metrics['throughput']
                throughput_results.append((impl, result.value))
                report.append(f"{impl:10} {result.value:8.1f} req/s")
        
        # Performance ranking
        if latency_results:
            report.append("")
            report.append("PERFORMANCE RANKING")
            report.append("-" * 30)
            
            # Best latency (lowest)
            best_latency = min(latency_results, key=lambda x: x[1])
            report.append(f"🏆 Lowest Latency:  {best_latency[0]} ({best_latency[1]:.2f}ms)")
            
            # Best throughput (highest)
            if throughput_results:
                best_throughput = max(throughput_results, key=lambda x: x[1])
                report.append(f"🚀 Highest Throughput: {best_throughput[0]} ({best_throughput[1]:.1f} req/s)")
        
        return "\n".join(report)
    
    def run_benchmarks(self) -> None:
        """Run benchmarks for all available implementations"""
        # Define implementations
        implementations = [
            ("go", "./bin/janus"),
            ("rust", "./RustJanus/target/debug/janus"),
            ("swift", "./SwiftJanus/.build/debug/SwiftJanusDgram")
        ]
        
        all_results = []
        
        for impl_name, binary_path in implementations:
            if os.path.exists(binary_path):
                results = self.benchmark_implementation(impl_name, binary_path)
                all_results.extend(results)
                self.results.extend(results)
            else:
                print(f"\n⚠️  Skipping {impl_name}: binary not found at {binary_path}")
        
        # Generate report
        if all_results:
            print("\n" + self.generate_report(all_results))
            
            # Save results
            results_data = [
                {
                    'implementation': r.implementation,
                    'metric': r.metric,
                    'value': r.value,
                    'unit': r.unit,
                    'details': r.details
                }
                for r in all_results
            ]
            
            with open('performance_results.json', 'w') as f:
                json.dump(results_data, f, indent=2)
            
            print(f"\n📊 Detailed results saved to: performance_results.json")
        else:
            print("\n❌ No benchmarks could be run")

def main():
    print("🚀 Starting Janus Cross-Platform Performance Benchmark")
    benchmark = SimpleBenchmark()
    benchmark.run_benchmarks()

if __name__ == "__main__":
    main()