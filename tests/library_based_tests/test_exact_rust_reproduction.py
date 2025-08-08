#!/usr/bin/env python3
"""Test using exact same process as cross-platform tests"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "orchestrator"))
from cross_platform_tests import run_cross_platform_test

def test_exact_reproduction():
    """Test TypeScript → Rust using exact same process as cross-platform tests"""
    
    print("🔍 Testing TypeScript → Rust using exact cross-platform test process...")
    
    os.chdir("/Users/bahram/ws/prj/Janus/tests/library_based_tests")
    base_dir = Path.cwd()
    
    # Use exact same function as the orchestrator
    success, details = run_cross_platform_test("typescript", "rust", base_dir)
    
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"Details: {details}")
    
    if not success:
        print("🔍 Additional error details:")
        if 'error' in details:
            print(f"Error: {details['error']}")
        if 'tests' in details:
            for test_name, test_result in details['tests'].items():
                if not test_result.get('success', True):
                    print(f"Test '{test_name}' failed: {test_result.get('error', 'No details')}")
    
    return success

if __name__ == "__main__":
    success = test_exact_reproduction()
    sys.exit(0 if success else 1)