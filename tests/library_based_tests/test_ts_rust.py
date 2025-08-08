#!/usr/bin/env python3
"""Test TypeScript to Rust combination"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "orchestrator"))
from cross_platform_tests import run_cross_platform_test

def test_ts_rust():
    os.chdir("/Users/bahram/ws/prj/Janus/tests/library_based_tests")
    base_dir = Path.cwd()
    
    print("Testing TypeScript → Rust...")
    success, details = run_cross_platform_test("typescript", "rust", base_dir)
    
    if success:
        print("✅ TypeScript → Rust: PASSED")
        return True
    else:
        print("❌ TypeScript → Rust: FAILED")
        print(f"Error: {details.get('error', 'No error details')}")
        print(f"Phase: {details.get('phase', 'Unknown')}")
        if 'tests' in details:
            for test_name, test_result in details['tests'].items():
                if not test_result.get('success', True):
                    print(f"Test '{test_name}' failed: {test_result.get('error', 'No details')}")
        return False

if __name__ == "__main__":
    success = test_ts_rust()
    sys.exit(0 if success else 1)