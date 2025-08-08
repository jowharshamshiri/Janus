#!/usr/bin/env python3
"""
Debug Swift server startListening issue
"""

import subprocess
import time
import os
import tempfile
from pathlib import Path

def test_swift_server_startup():
    """Test if Swift server can start without hanging"""
    
    test_dir = Path(tempfile.mkdtemp())
    socket_path = str(test_dir / "debug_server.sock")
    
    print(f"Testing Swift server startup in {test_dir}")
    print(f"Socket path: {socket_path}")
    
    try:
        # Use existing test server
        server_dir = Path("/Users/bahram/ws/prj/Janus/tests/library_based_tests/swift")
        
        print("Building Swift test server...")
        build_result = subprocess.run([
            "swift", "build", "--package-path", str(server_dir)
        ], capture_output=True, text=True, timeout=30)
        
        if build_result.returncode != 0:
            print(f"❌ Build failed: {build_result.stderr}")
            return False
        
        print("✅ Build successful")
        
        # Start server with timeout
        print("Starting Swift server...")
        server_process = subprocess.Popen([
            "swift", "run", "--package-path", str(server_dir), 
            "TestServer", socket_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for SERVER_READY with timeout
        start_time = time.time()
        server_ready = False
        output_lines = []
        
        while time.time() - start_time < 15:
            if server_process.poll() is not None:
                stdout, stderr = server_process.communicate()
                print(f"❌ Server exited early")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False
            
            # Check for socket file existence
            if os.path.exists(socket_path):
                print("✅ Socket file created")
                server_ready = True
                break
            
            time.sleep(0.1)
        
        if not server_ready:
            print("❌ Server failed to create socket within timeout")
            try:
                stdout, stderr = server_process.communicate(timeout=2)
                print(f"Server output: {stdout}")
                print(f"Server errors: {stderr}")
            except:
                print("Server still running, killing...")
                server_process.kill()
            return False
        
        print("✅ Swift server started successfully")
        
        # Let it run for a moment to ensure it's stable
        time.sleep(2)
        
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            print(f"❌ Server died after startup: {stderr}")
            return False
        
        print("✅ Swift server is stable and running")
        
        # Kill server
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()
        
        return True
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    finally:
        try:
            os.remove(socket_path)
        except:
            pass

if __name__ == "__main__":
    success = test_swift_server_startup()
    exit(0 if success else 1)