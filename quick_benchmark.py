#!/usr/bin/env python3
"""
Quick Janus Performance Benchmark
"""

import json
import socket
import os
import time
import subprocess
import threading
import statistics
from typing import List, Tuple

def run_server(binary_path: str, socket_path: str) -> subprocess.Popen:
    """Start server"""
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

def measure_latency(socket_path: str, iterations: int = 50) -> Tuple[float, int]:
    """Measure ping latency"""
    latencies = []
    failures = 0
    
    for i in range(iterations):
        try:
            start = time.perf_counter()
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            reply_path = f"/tmp/bench_{i}.sock"
            
            sock.bind(reply_path)
            import uuid
            msg = {
                'id': str(uuid.uuid4()),
                'channelId': 'system',
                'request': 'ping',
                'reply_to': reply_path,
                'args': {'message': 'benchmark'},
                'timestamp': time.time()
            }
            
            sock.sendto(json.dumps(msg).encode(), socket_path)
            sock.settimeout(1.0)
            response, _ = sock.recvfrom(4096)
            end = time.perf_counter()
            
            data = json.loads(response.decode())
            if data.get('success') or 'pong' in str(data):
                latencies.append((end - start) * 1000)
            else:
                failures += 1
                
        except Exception:
            failures += 1
        finally:
            try:
                sock.close()
                os.unlink(reply_path)
            except:
                pass
    
    if latencies:
        return statistics.mean(latencies), failures
    return 0, failures

def benchmark_impl(name: str, binary_path: str) -> None:
    """Benchmark one implementation"""
    print(f"\n🚀 Benchmarking {name.upper()}")
    socket_path = f"/tmp/bench_{name}.sock"
    
    # Start server
    proc = run_server(binary_path, socket_path)
    if not proc:
        print(f"❌ Failed to start {name} server")
        return
    
    try:
        # Run benchmark
        avg_latency, failures = measure_latency(socket_path, 50)
        
        if avg_latency > 0:
            print(f"✅ {name:8} {avg_latency:8.2f}ms avg latency  ({failures} failures)")
        else:
            print(f"❌ {name:8} All requests failed ({failures}/50)")
            
    finally:
        proc.terminate()
        try:
            os.unlink(socket_path)
        except:
            pass
        time.sleep(0.1)

def main():
    print("⚡ Quick Janus Performance Benchmark")
    
    implementations = [
        ("go", "./bin/janus"),
        ("rust", "./RustJanus/target/debug/janus"),
        ("swift", "./SwiftJanus/.build/debug/SwiftJanusDgram")
    ]
    
    results = []
    
    for name, binary_path in implementations:
        if os.path.exists(binary_path):
            benchmark_impl(name, binary_path)
        else:
            print(f"⚠️  Skipping {name}: binary not found")
    
    print("\n📊 Benchmark Complete")

if __name__ == "__main__":
    main()