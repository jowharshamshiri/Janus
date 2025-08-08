#!/usr/bin/env python3
"""
Single combination test to debug failures
"""

import subprocess
import sys
import os
import tempfile
import time
from pathlib import Path

def test_go_to_swift():
    """Test Go client to Swift server"""
    print("Testing Go client → Swift server...")
    
    # Test directory
    test_dir = Path(tempfile.mkdtemp())
    socket_path = str(test_dir / "test_server.sock")
    
    try:
        # Create Swift server
        swift_server_code = '''
import Foundation
import SwiftJanus

let socketPath = CommandLine.arguments[1]

// Remove existing socket
try? FileManager.default.removeItem(atPath: socketPath)

let server = JanusServer()

Task {
    do {
        try await server.startListening(socketPath)
    } catch {
        print("Server error: \\(error)")
        exit(1)
    }
}

print("SERVER_READY")

// Keep server running
RunLoop.main.run()
'''
        
        server_file = test_dir / "server.swift" 
        server_file.write_text(swift_server_code)
        
        print(f"Building Swift server in {test_dir}...")
        
        # Build Swift server
        build_result = subprocess.run([
            "swift", "build", "--package-path", "/Users/bahram/ws/prj/Janus/SwiftJanus", 
            "--product", "SwiftJanus"
        ], capture_output=True, text=True, timeout=30)
        
        if build_result.returncode != 0:
            print(f"❌ Swift build failed: {build_result.stderr}")
            return False
        
        print("✅ Swift server built successfully")
        
        # Try to start Swift server
        server_process = subprocess.Popen([
            "swift", "run", "--package-path", "/Users/bahram/ws/prj/Janus/SwiftJanus",
            "-c", server_file.read_text()
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for "SERVER_READY"
        start_time = time.time()
        server_ready = False
        
        while time.time() - start_time < 10:
            if server_process.poll() is not None:
                stdout, stderr = server_process.communicate()
                print(f"❌ Swift server exited early: {stderr}")
                return False
                
            # Check if socket exists
            if os.path.exists(socket_path):
                server_ready = True
                break
                
            time.sleep(0.1)
        
        if not server_ready:
            print("❌ Swift server failed to start")
            server_process.terminate()
            return False
        
        print("✅ Swift server started successfully")
        
        # Now test Go client
        go_client_code = f'''
package main

import (
    "context"
    "fmt"
    "GoJanus/pkg/protocol"
)

func main() {{
    client := protocol.New("{socket_path}")
    
    ctx := context.Background()
    response, err := client.SendRequest(ctx, "ping", nil)
    if err != nil {{
        fmt.Printf("ERROR: %v\\n", err)
        return
    }}
    
    fmt.Printf("SUCCESS: %v\\n", response)
}}
'''
        
        client_file = test_dir / "client.go"
        client_file.write_text(go_client_code)
        
        # Build Go client
        client_build = subprocess.run([
            "go", "build", "-o", "test_client", "client.go"
        ], cwd=test_dir, capture_output=True, text=True)
        
        if client_build.returncode != 0:
            print(f"❌ Go client build failed: {client_build.stderr}")
            server_process.terminate()
            return False
        
        # Run Go client
        client_result = subprocess.run([
            "./test_client"
        ], cwd=test_dir, capture_output=True, text=True, timeout=10)
        
        if client_result.returncode == 0 and "SUCCESS" in client_result.stdout:
            print("✅ Go client → Swift server communication successful")
            success = True
        else:
            print(f"❌ Go client failed: {client_result.stdout} {client_result.stderr}")
            success = False
        
        # Cleanup
        server_process.terminate()
        return success
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    finally:
        # Cleanup
        try:
            os.remove(socket_path)
        except:
            pass

if __name__ == "__main__":
    success = test_go_to_swift()
    sys.exit(0 if success else 1)