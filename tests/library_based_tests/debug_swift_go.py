#!/usr/bin/env python3
"""
Debug Swift client to Go server communication
"""

import subprocess
import time
import os
import tempfile
from pathlib import Path

def test_swift_to_go():
    """Test Swift client to Go server"""
    
    test_dir = Path(tempfile.mkdtemp())
    socket_path = str(test_dir / "go_server.sock")
    
    print(f"Testing Swift client → Go server in {test_dir}")
    
    try:
        # Create Go server code
        go_server_code = '''
package main

import (
    "fmt"
    "log"
    "os"
    "os/signal"
    "syscall"
    "GoJanus/pkg/server"
)

func main() {
    socketPath := os.Args[1]
    
    // Remove existing socket
    os.Remove(socketPath)
    
    config := &server.ServerConfig{
        SocketPath: socketPath,
    }
    srv := server.NewJanusServer(config)
    
    // Start server
    if err := srv.StartListening(); err != nil {
        log.Fatalf("Failed to start server: %v", err)
    }
    
    fmt.Println("SERVER_READY")
    
    // Wait for signal
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
    <-sigChan
    
    srv.Stop()
}
'''
        
        # Write Go server file
        server_file = test_dir / "server.go"
        server_file.write_text(go_server_code)
        
        print("Building Go server...")
        build_result = subprocess.run([
            "go", "build", "-o", "test_server", "server.go"
        ], cwd=test_dir, capture_output=True, text=True, timeout=30)
        
        if build_result.returncode != 0:
            print(f"❌ Go build failed: {build_result.stderr}")
            return False
        
        print("✅ Go server built")
        
        # Start Go server
        server_process = subprocess.Popen([
            "./test_server", socket_path
        ], cwd=test_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for server ready
        start_time = time.time()
        server_ready = False
        
        while time.time() - start_time < 10:
            if server_process.poll() is not None:
                stdout, stderr = server_process.communicate()
                print(f"❌ Go server exited: {stderr}")
                return False
            
            if os.path.exists(socket_path):
                server_ready = True
                break
            
            time.sleep(0.1)
        
        if not server_ready:
            print("❌ Go server failed to start")
            server_process.terminate()
            return False
        
        print("✅ Go server started")
        
        # Create Swift client code
        swift_client_code = f'''
import Foundation
import SwiftJanus

@main
struct ClientApp {{
    static func main() async {{
        let client = JanusClient(socketPath: "{socket_path}")
        
        do {{
            let result = try await client.sendRequest("ping", args: [:])
            print("SUCCESS: \\(result)")
        }} catch {{
            print("ERROR: \\(error)")
            exit(1)
        }}
    }}
}}
'''
        
        # Create Swift client test directory
        swift_dir = test_dir / "SwiftClient"
        swift_dir.mkdir()
        
        # Create Package.swift
        package_swift = '''
// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "SwiftClient",
    platforms: [
        .macOS(.v12)
    ],
    dependencies: [
        .package(path: "/Users/bahram/ws/prj/Janus/SwiftJanus")
    ],
    targets: [
        .executableTarget(
            name: "SwiftClient",
            dependencies: ["SwiftJanus"],
            path: "Sources"
        )
    ]
)
'''
        
        (swift_dir / "Package.swift").write_text(package_swift)
        (swift_dir / "Sources").mkdir()
        (swift_dir / "Sources" / "main.swift").write_text(swift_client_code)
        
        print("Building Swift client...")
        swift_build = subprocess.run([
            "swift", "build", "--package-path", str(swift_dir)
        ], capture_output=True, text=True, timeout=30)
        
        if swift_build.returncode != 0:
            print(f"❌ Swift build failed: {swift_build.stderr}")
            server_process.terminate()
            return False
        
        print("✅ Swift client built")
        
        # Run Swift client
        print("Running Swift client...")
        client_result = subprocess.run([
            "swift", "run", "--package-path", str(swift_dir), "SwiftClient"
        ], capture_output=True, text=True, timeout=15)
        
        print(f"Client return code: {client_result.returncode}")
        print(f"Client stdout: {client_result.stdout}")
        print(f"Client stderr: {client_result.stderr}")
        
        # Clean up
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except:
            server_process.kill()
        
        if client_result.returncode == 0 and "SUCCESS" in client_result.stdout:
            print("✅ Swift client → Go server communication successful")
            return True
        else:
            print("❌ Communication failed")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    finally:
        try:
            os.remove(socket_path)
        except:
            pass

if __name__ == "__main__":
    success = test_swift_to_go()
    exit(0 if success else 1)