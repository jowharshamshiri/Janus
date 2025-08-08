#!/usr/bin/env python3
"""
Debug Swift client to Go server communication with fixed Go imports
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
        # Create Go server using the GoJanus directory directly
        go_janus_dir = Path("/Users/bahram/ws/prj/Janus/GoJanus")
        
        # Create go.mod file
        go_mod = '''
module test_server

go 1.21

replace GoJanus => /Users/bahram/ws/prj/Janus/GoJanus

require GoJanus v0.0.0-00010101000000-000000000000
'''
        
        (test_dir / "go.mod").write_text(go_mod.strip())
        
        # Create Go server code with proper imports
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
        server_file = test_dir / "main.go"
        server_file.write_text(go_server_code)
        
        print("Building Go server...")
        
        # First run go mod tidy
        tidy_result = subprocess.run([
            "go", "mod", "tidy"
        ], cwd=test_dir, capture_output=True, text=True, timeout=30)
        
        if tidy_result.returncode != 0:
            print(f"❌ go mod tidy failed: {tidy_result.stderr}")
            return False
        
        build_result = subprocess.run([
            "go", "build", "-o", "test_server", "main.go"
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
                print(f"❌ Go server exited: {stdout} | {stderr}")
                return False
            
            if os.path.exists(socket_path):
                server_ready = True
                print("✅ Go server socket created")
                break
            
            time.sleep(0.1)
        
        if not server_ready:
            print("❌ Go server failed to start")
            server_process.terminate()
            return False
        
        print("✅ Go server started")
        
        # Now test Swift client - use existing test client
        swift_test_dir = Path("/Users/bahram/ws/prj/Janus/tests/library_based_tests/swift")
        
        print("Testing Swift client...")
        client_result = subprocess.run([
            "swift", "run", "--package-path", str(swift_test_dir), "TestClient", socket_path, "ping"
        ], capture_output=True, text=True, timeout=15)
        
        print(f"Swift client return code: {client_result.returncode}")
        print(f"Swift client stdout: {client_result.stdout}")
        print(f"Swift client stderr: {client_result.stderr}")
        
        # Clean up server
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except:
            server_process.kill()
        
        if client_result.returncode == 0:
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