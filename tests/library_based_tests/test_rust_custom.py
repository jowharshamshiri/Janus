#!/usr/bin/env python3
"""Test Rust server custom handler with TypeScript client"""

import subprocess
import time
import os
import tempfile
from pathlib import Path

def test_rust_server_with_ts_client():
    """Test Rust server custom handler with actual TypeScript client"""
    
    test_dir = Path(tempfile.mkdtemp())
    socket_path = str(test_dir / "rust_server.sock")
    
    print(f"Testing Rust server + TypeScript client in {test_dir}")
    
    try:
        # Build and start Rust server (using the debug server from previous test)
        rust_dir = Path("/Users/bahram/ws/prj/Janus/tests/library_based_tests/rust")
        
        print("Starting Rust server...")
        server_process = subprocess.Popen([
            "./target/debug/debug_server", socket_path
        ], cwd=rust_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for server ready
        start_time = time.time()
        server_ready = False
        
        while time.time() - start_time < 10:
            if server_process.poll() is not None:
                stdout, stderr = server_process.communicate()
                print(f"❌ Server exited: {stdout} | {stderr}")
                return False
            
            if os.path.exists(socket_path):
                server_ready = True
                break
            
            time.sleep(0.1)
        
        if not server_ready:
            print("❌ Server failed to start")
            server_process.terminate()
            return False
        
        print("✅ Rust server started")
        
        # Now test with TypeScript client
        ts_dir = Path("/Users/bahram/ws/prj/Janus/TypeScriptJanus")
        
        print("Testing with TypeScript client...")
        
        # Use the existing TypeScript test client
        client_result = subprocess.run([
            "npm", "run", "test:custom_test", socket_path
        ], cwd=ts_dir, capture_output=True, text=True, timeout=10)
        
        print(f"TS Client return code: {client_result.returncode}")
        print(f"TS Client stdout: {client_result.stdout}")
        print(f"TS Client stderr: {client_result.stderr}")
        
        # Try alternative - direct node execution
        if client_result.returncode != 0:
            # Create simple TypeScript client script
            client_script = f'''
const {{ JanusClient }} = require('./dist/index.js');

async function testCustom() {{
    try {{
        const client = new JanusClient('{socket_path}');
        const result = await client.sendRequest('custom_test', {{ test_param: 'from_typescript' }});
        console.log('SUCCESS:', JSON.stringify(result));
    }} catch (error) {{
        console.log('ERROR:', error.message);
        process.exit(1);
    }}
}}

testCustom();
'''
            
            script_file = test_dir / "test_client.js"
            script_file.write_text(client_script)
            
            client_result = subprocess.run([
                "node", str(script_file)
            ], cwd=ts_dir, capture_output=True, text=True, timeout=10)
            
            print(f"Direct node return code: {client_result.returncode}")
            print(f"Direct node stdout: {client_result.stdout}")
            print(f"Direct node stderr: {client_result.stderr}")
        
        # Get server output
        time.sleep(1)
        if server_process.poll() is None:
            # Server still running, get partial output
            print("Server still running - getting partial output")
        else:
            stdout, stderr = server_process.communicate()
            print(f"Server output: {stdout}")
            print(f"Server errors: {stderr}")
        
        # Clean up
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()
        
        success = "SUCCESS" in client_result.stdout
        print(f"Test {'PASSED' if success else 'FAILED'}")
        return success
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    finally:
        try:
            os.remove(socket_path)
        except:
            pass

if __name__ == "__main__":
    success = test_rust_server_with_ts_client()
    exit(0 if success else 1)