#!/usr/bin/env python3
"""Test if Rust server responds to manifest request"""

import subprocess
import time
import os
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "orchestrator"))
from cross_platform_tests import ServerManager

def test_rust_manifest():
    """Test if Rust server responds to built-in manifest request"""
    
    socket_path = f"/tmp/rust_manifest_{os.getpid()}.sock"
    
    print(f"Testing Rust server manifest response...")
    
    try:
        # Start Rust server using the ServerManager
        server = ServerManager("rust", socket_path)
        base_dir = Path.cwd()
        server_dir = base_dir / "rust"
        
        if not server.start(server_dir):
            print(f"❌ Failed to start Rust server: {server.error_message}")
            return False
        
        print("✅ Rust server started")
        
        # Test with a manual Go client to the Rust server (we know Go works)
        go_test_code = f'''
package main

import (
    "context"
    "fmt"
    "GoJanus/pkg/protocol"
)

func main() {{
    client := protocol.New("{socket_path}")
    
    ctx := context.Background()
    
    // Test manifest
    manifestResponse, err := client.SendRequest(ctx, "manifest", nil)
    if err != nil {{
        fmt.Printf("MANIFEST_ERROR: %v\\n", err)
    }} else {{
        fmt.Printf("MANIFEST_SUCCESS: %v\\n", manifestResponse.Success)
    }}
    
    // Test ping
    pingResponse, err := client.SendRequest(ctx, "ping", nil)
    if err != nil {{
        fmt.Printf("PING_ERROR: %v\\n", err)
    }} else {{
        fmt.Printf("PING_SUCCESS: %v\\n", pingResponse.Success)
    }}
    
    // Test custom_test
    customResponse, err := client.SendRequest(ctx, "custom_test", map[string]interface{}{{"test_param": "go_client"}})
    if err != nil {{
        fmt.Printf("CUSTOM_ERROR: %v\\n", err)
    }} else {{
        fmt.Printf("CUSTOM_SUCCESS: %v\\n", customResponse.Success)
    }}
}}
'''
        
        # Create temp directory for Go client
        test_dir = Path(tempfile.mkdtemp())
        
        # Create go.mod file
        go_mod = '''
module test_client

go 1.21

replace GoJanus => /Users/bahram/ws/prj/Janus/GoJanus

require GoJanus v0.0.0-00010101000000-000000000000
'''
        
        (test_dir / "go.mod").write_text(go_mod.strip())
        (test_dir / "main.go").write_text(go_test_code)
        
        # Build and run Go client
        subprocess.run(["go", "mod", "tidy"], cwd=test_dir, capture_output=True)
        build_result = subprocess.run(["go", "build", "-o", "client", "main.go"], 
                                    cwd=test_dir, capture_output=True, text=True)
        
        if build_result.returncode != 0:
            print(f"❌ Go client build failed: {build_result.stderr}")
            return False
        
        # Run client
        result = subprocess.run(["./client"], cwd=test_dir, capture_output=True, text=True, timeout=10)
        
        print(f"Go client output:\n{result.stdout}")
        print(f"Go client errors:\n{result.stderr}")
        
        # Check results
        success = ("MANIFEST_SUCCESS: true" in result.stdout and 
                  "PING_SUCCESS: true" in result.stdout and
                  "CUSTOM_SUCCESS: true" in result.stdout)
        
        return success
        
    finally:
        server.stop()
        try:
            os.remove(socket_path)
        except:
            pass

if __name__ == "__main__":
    success = test_rust_manifest()
    print(f"Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)