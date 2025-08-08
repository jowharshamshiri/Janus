#!/usr/bin/env python3
"""Test TypeScript to Swift combination"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "orchestrator"))
from cross_platform_tests import run_cross_platform_test

def test_ts_swift():
    os.chdir("/Users/bahram/ws/prj/Janus/tests/library_based_tests")
    base_dir = Path.cwd()
    
    print("Testing TypeScript → Swift...")
    success, details = run_cross_platform_test("typescript", "swift", base_dir)
    
    if success:
        print("✅ TypeScript → Swift: PASSED")
        return True
    else:
        print("❌ TypeScript → Swift: FAILED")
        print(f"Error: {details.get('error', 'No error details')}")
        print(f"Phase: {details.get('phase', 'Unknown')}")
        return False

if __name__ == "__main__":
    success = test_ts_swift()
    sys.exit(0 if success else 1)