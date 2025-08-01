#!/usr/bin/env python3
"""
Comprehensive Janus Cross-Platform Performance Benchmark
Measures latency, throughput, and concurrent performance across Go, Rust, Swift implementations
"""

import json
import socket
import os
import time
import subprocess
import threading
import statistics
import uuid
from typing import Dict, List, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class BenchmarkResult:
    """Performance benchmark result"""
    implementation: str
    test_type: str
    metric: str
    value: float
    unit: str
    details: Dict = None

class ComprehensiveBenchmark:
    """Comprehensive performance benchmark for Janus implementations"""
    
    def __init__(self):
        self.results = []
        
    def run_server(self, binary_path: str, socket_path: str) -> subprocess.Popen:
        """Start server process"""
        try:
            os.unlink(socket_path)
        except FileNotFoundError:
            pass
        
        proc = subprocess.Popen(
            [binary_path, "--listen", "--socket", socket_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait for socket
        for _ in range(50):
            if os.path.exists(socket_path):
                time.sleep(0.2)
                return proc
            time.sleep(0.1)
        
        proc.terminate()
        return None
    
    def send_request(self, socket_path: str, command: str = "ping") -> Tuple[bool, float]:
        """Send single request and measure latency"""
        start = time.perf_counter()
        
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            reply_path = f"/tmp/bench_{threading.get_ident()}_{int(time.time() * 1000000)}.sock"
            
            sock.bind(reply_path)
            
            msg = {
                'id': str(uuid.uuid4()),
                'channelId': 'system',
                'command': command,
                'reply_to': reply_path,
                'args': {'message': 'benchmark'},
                'timestamp': time.time()
            }
            
            sock.sendto(json.dumps(msg).encode(), socket_path)
            sock.settimeout(2.0)
            response, _ = sock.recvfrom(4096)
            end = time.perf_counter()
            
            data = json.loads(response.decode())
            success = data.get('success', False) or 'pong' in str(data)
            
            return success, end - start
            
        except Exception:
            return False, time.perf_counter() - start
        finally:
            try:
                sock.close()
                os.unlink(reply_path)
            except:
                pass
    
    def latency_benchmark(self, impl_name: str, socket_path: str, iterations: int = 200) -> BenchmarkResult:
        """Measure request-response latency"""
        print(f"  Running latency test ({iterations} requests)...")
        
        latencies = []
        failures = 0
        
        for _ in range(iterations):
            success, latency = self.send_request(socket_path)
            if success:
                latencies.append(latency * 1000)  # Convert to ms
            else:
                failures += 1
        
        if not latencies:
            return BenchmarkResult(
                implementation=impl_name,
                test_type="latency",
                metric="error",
                value=100.0,
                unit="percent_failed",
                details={"failures": failures, "total": iterations}
            )
        
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
        
        return BenchmarkResult(
            implementation=impl_name,
            test_type="latency",
            metric="avg_latency_ms",
            value=avg_latency,
            unit="milliseconds",
            details={
                "p95_ms": p95_latency,
                "p99_ms": p99_latency,
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "median_ms": statistics.median(latencies),
                "stddev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "success_rate": len(latencies) / iterations,
                "failures": failures
            }
        )
    
    def throughput_benchmark(self, impl_name: str, socket_path: str, duration: int = 15) -> BenchmarkResult:
        """Measure sustained throughput"""
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
            time.sleep(0.001)  # Small delay to prevent overwhelming
        
        actual_duration = time.perf_counter() - start_time
        throughput = successful_requests / actual_duration
        
        return BenchmarkResult(
            implementation=impl_name,
            test_type="throughput",
            metric="requests_per_second",
            value=throughput,
            unit="req/s",
            details={
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "duration": actual_duration,
                "success_rate": successful_requests / total_requests if total_requests > 0 else 0
            }
        )
    
    def concurrent_benchmark(self, impl_name: str, socket_path: str, concurrent_clients: int = 20, requests_per_client: int = 25) -> BenchmarkResult:
        """Measure concurrent request handling"""
        print(f"  Running concurrency test ({concurrent_clients} clients, {requests_per_client} req/client)...")
        
        def client_worker():
            successful = 0
            failed = 0
            latencies = []
            
            for _ in range(requests_per_client):
                success, latency = self.send_request(socket_path)
                if success:
                    successful += 1
                    latencies.append(latency * 1000)
                else:
                    failed += 1
                    
            return successful, failed, latencies
        
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=concurrent_clients) as executor:
            futures = [executor.submit(client_worker) for _ in range(concurrent_clients)]
            
            total_successful = 0
            total_failed = 0
            all_latencies = []
            
            for future in as_completed(futures):
                try:
                    successful, failed, latencies = future.result()
                    total_successful += successful
                    total_failed += failed
                    all_latencies.extend(latencies)
                except Exception:
                    total_failed += requests_per_client
        
        duration = time.perf_counter() - start_time
        total_requests = total_successful + total_failed
        success_rate = total_successful / total_requests if total_requests > 0 else 0
        
        return BenchmarkResult(
            implementation=impl_name,
            test_type="concurrency",
            metric="success_rate",
            value=success_rate,
            unit="percent",
            details={
                "total_requests": total_requests,
                "successful_requests": total_successful,
                "failed_requests": total_failed,
                "concurrent_clients": concurrent_clients,
                "requests_per_client": requests_per_client,
                "duration": duration,
                "avg_latency_ms": statistics.mean(all_latencies) if all_latencies else 0,
                "throughput_rps": total_successful / duration if duration > 0 else 0
            }
        )
    
    def benchmark_implementation(self, impl_name: str, binary_path: str) -> List[BenchmarkResult]:
        """Run all benchmarks for one implementation"""
        print(f"\n{'='*60}")
        print(f"BENCHMARKING {impl_name.upper()}")
        print(f"{'='*60}")
        
        socket_path = f"/tmp/benchmark_{impl_name}.sock"
        results = []
        
        # Start server
        proc = self.run_server(binary_path, socket_path)
        if not proc:
            print(f"❌ Failed to start {impl_name} server")
            return [BenchmarkResult(
                implementation=impl_name,
                test_type="server",
                metric="startup_error",
                value=1,
                unit="boolean",
                details={"error": "Server failed to start"}
            )]
        
        try:
            # Latency test
            latency_result = self.latency_benchmark(impl_name, socket_path, 200)
            results.append(latency_result)
            
            if latency_result.metric != "error":
                print(f"  ✅ Latency: {latency_result.value:.2f}ms avg, {latency_result.details['p95_ms']:.2f}ms p95, {latency_result.details['p99_ms']:.2f}ms p99")
            else:
                print(f"  ❌ Latency test failed")
                return results
            
            # Throughput test
            throughput_result = self.throughput_benchmark(impl_name, socket_path, 15)
            results.append(throughput_result)
            print(f"  ✅ Throughput: {throughput_result.value:.1f} req/s ({throughput_result.details['success_rate']:.1%} success)")
            
            # Concurrency test
            concurrency_result = self.concurrent_benchmark(impl_name, socket_path, 20, 25)
            results.append(concurrency_result)
            print(f"  ✅ Concurrency: {concurrency_result.value:.1%} success rate, {concurrency_result.details['throughput_rps']:.1f} req/s under load")
            
        finally:
            # Cleanup
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            except Exception:
                pass
            
            try:
                os.unlink(socket_path)
            except FileNotFoundError:
                pass
        
        return results
    
    def generate_report(self, all_results: List[BenchmarkResult]) -> str:
        """Generate comprehensive performance report"""
        report = []
        report.append("=" * 80)
        report.append("JANUS CROSS-PLATFORM PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
        report.append("")
        
        # Group by implementation
        by_impl = {}
        for result in all_results:
            if result.implementation not in by_impl:
                by_impl[result.implementation] = {}
            by_impl[result.implementation][result.test_type] = result
        
        # Performance summary table
        report.append("PERFORMANCE SUMMARY")
        report.append("=" * 50)
        report.append(f"{'Implementation':12} {'Latency (ms)':>12} {'P95 (ms)':>10} {'Throughput':>12} {'Concurrency':>12}")
        report.append("-" * 70)
        
        for impl_name, results in by_impl.items():
            latency = results.get('latency')
            throughput = results.get('throughput')
            concurrency = results.get('concurrency')
            
            lat_val = f"{latency.value:.2f}" if latency and latency.metric != "error" else "FAILED"
            p95_val = f"{latency.details['p95_ms']:.2f}" if latency and latency.metric != "error" else "-"
            thr_val = f"{throughput.value:.0f} req/s" if throughput else "-"
            con_val = f"{concurrency.value:.1%}" if concurrency else "-"
            
            report.append(f"{impl_name:12} {lat_val:>12} {p95_val:>10} {thr_val:>12} {con_val:>12}")
        
        # Detailed results
        report.append("\nDETAILED RESULTS")
        report.append("=" * 50)
        
        for impl_name, results in by_impl.items():
            report.append(f"\n{impl_name.upper()} IMPLEMENTATION")
            report.append("-" * 30)
            
            for test_type, result in results.items():
                if result.metric == "error" or result.metric == "startup_error":
                    report.append(f"  {test_type.title()}: FAILED")
                else:
                    report.append(f"  {test_type.title()}: {result.value:.2f} {result.unit}")
                    if result.details:
                        for key, value in result.details.items():
                            if key in ['p95_ms', 'p99_ms', 'median_ms', 'success_rate', 'throughput_rps', 'concurrent_clients']:
                                if isinstance(value, float):
                                    report.append(f"    {key}: {value:.2f}")
                                else:
                                    report.append(f"    {key}: {value}")
        
        # Performance ranking
        report.append("\nPERFORMANCE RANKING")
        report.append("=" * 30)
        
        # Collect successful results for ranking
        latency_results = [(impl, res['latency'].value) for impl, res in by_impl.items() 
                          if 'latency' in res and res['latency'].metric != "error"]
        throughput_results = [(impl, res['throughput'].value) for impl, res in by_impl.items() 
                             if 'throughput' in res]
        concurrency_results = [(impl, res['concurrency'].value) for impl, res in by_impl.items() 
                              if 'concurrency' in res]
        
        if latency_results:
            best_latency = min(latency_results, key=lambda x: x[1])
            report.append(f"🏆 Lowest Latency:    {best_latency[0]} ({best_latency[1]:.2f}ms)")
        
        if throughput_results:
            best_throughput = max(throughput_results, key=lambda x: x[1])
            report.append(f"🚀 Highest Throughput: {best_throughput[0]} ({best_throughput[1]:.0f} req/s)")
        
        if concurrency_results:
            best_concurrency = max(concurrency_results, key=lambda x: x[1])
            report.append(f"⚡ Best Concurrency:   {best_concurrency[0]} ({best_concurrency[1]:.1%} success)")
        
        return "\n".join(report)
    
    def run_benchmarks(self) -> None:
        """Run comprehensive benchmarks for all implementations"""
        print("🚀 Starting Janus Comprehensive Performance Benchmark")
        
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
        
        if all_results:
            # Generate and display report
            report = self.generate_report(all_results)
            print("\n" + report)
            
            # Save detailed results
            results_data = [
                {
                    'implementation': r.implementation,
                    'test_type': r.test_type,
                    'metric': r.metric,
                    'value': r.value,
                    'unit': r.unit,
                    'details': r.details
                }
                for r in all_results
            ]
            
            with open('comprehensive_benchmark_results.json', 'w') as f:
                json.dump(results_data, f, indent=2)
            
            with open('performance_report.txt', 'w') as f:
                f.write(report)
            
            print(f"\n📊 Detailed results saved to: comprehensive_benchmark_results.json")
            print(f"📋 Report saved to: performance_report.txt")
        else:
            print("\n❌ No benchmarks could be run")

def main():
    benchmark = ComprehensiveBenchmark()
    benchmark.run_benchmarks()

if __name__ == "__main__":
    main()