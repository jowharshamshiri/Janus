#!/usr/bin/env python3
"""Test Go to Rust specifically"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "orchestrator"))
from cross_platform_tests import run_cross_platform_test

def test_go_rust():
    """Test Go → Rust specifically"""
    
    print("🔍 Testing Go → Rust combination...")
    
    os.chdir("/Users/bahram/ws/prj/Janus/tests/library_based_tests")
    base_dir = Path.cwd()
    
    success, details = run_cross_platform_test("go", "rust", base_dir)
    
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"Details: {details}")
    
    if not success:
        print("🔍 Additional error details:")
        if 'error' in details:
            print(f"Error: {details['error']}")
    
    return success

if __name__ == "__main__":
    success = test_go_rust()
    sys.exit(0 if success else 1)