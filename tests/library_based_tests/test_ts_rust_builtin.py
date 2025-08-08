#!/usr/bin/env python3
"""Test TypeScript to Rust with built-in method first"""

import sys
import os
from pathlib import Path
import subprocess
import time
import tempfile

sys.path.insert(0, str(Path.cwd() / "orchestrator"))
from cross_platform_tests import run_cross_platform_test, ServerManager

def test_rust_server_builtin():
    """Test if Rust server responds to built-in methods"""
    
    base_dir = Path.cwd()
    socket_path = f"/tmp/debug_rust_builtin_{os.getpid()}.sock"
    
    print("Testing Rust server built-in methods...")
    
    # Start Rust server
    server = ServerManager("rust", socket_path)
    server_dir = base_dir / "rust"
    
    if not server.start(server_dir):
        print(f"❌ Failed to start Rust server: {server.error_message}")
        return False
    
    try:
        # Test with simple ping first
        ts_dir = Path("/Users/bahram/ws/prj/Janus/TypeScriptJanus")
        
        # Create simple test script
        test_dir = Path(tempfile.mkdtemp())
        client_script = f'''
const {{ JanusClient }} = require('{ts_dir}/dist/index.js');

async function testBuiltins() {{
    try {{
        const client = new JanusClient('{socket_path}');
        
        console.log('Testing ping...');
        const pingResult = await client.sendRequest('ping');
        console.log('PING_SUCCESS:', JSON.stringify(pingResult));
        
        console.log('Testing manifest...');
        const manifestResult = await client.sendRequest('manifest');
        console.log('MANIFEST_SUCCESS:', JSON.stringify(manifestResult));
        
        console.log('Testing echo...');
        const echoResult = await client.sendRequest('echo', {{ message: 'test' }});
        console.log('ECHO_SUCCESS:', JSON.stringify(echoResult));
        
        console.log('Testing custom_test...');
        const customResult = await client.sendRequest('custom_test', {{ test_param: 'from_typescript' }});
        console.log('CUSTOM_SUCCESS:', JSON.stringify(customResult));
        
        await client.disconnect();
    }} catch (error) {{
        console.log('ERROR:', error.message, error.code);
        process.exit(1);
    }}
}}

testBuiltins();
'''
        
        script_file = test_dir / "test_builtin.js"
        script_file.write_text(client_script)
        
        # Run test
        result = subprocess.run([
            "node", str(script_file)
        ], capture_output=True, text=True, timeout=15)
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        
        return "CUSTOM_SUCCESS" in result.stdout
        
    finally:
        server.stop()

if __name__ == "__main__":
    success = test_rust_server_builtin()
    print(f"Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)