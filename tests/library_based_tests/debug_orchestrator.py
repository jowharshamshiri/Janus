#!/usr/bin/env python3
"""
Debug orchestrator with detailed failure reporting
"""

import subprocess
import json
import sys
import os
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path.cwd() / "orchestrator"))

from cross_platform_tests import run_cross_platform_test

def debug_combinations():
    """Test each combination individually with detailed error reporting"""
    
    base_dir = Path.cwd()
    combinations = [
        ("go", "go"),
        ("go", "rust"), 
        ("go", "swift"),
        ("go", "typescript"),
        ("rust", "rust"),
        ("rust", "go"),
        ("rust", "swift"), 
        ("rust", "typescript"),
        ("swift", "go"),
        ("swift", "rust"),
        ("swift", "swift"),
        ("swift", "typescript"),
        ("typescript", "go"),
        ("typescript", "rust"),
        ("typescript", "swift"),
        ("typescript", "typescript"),
    ]
    
    passed = 0
    failed = 0
    
    print("=== DETAILED CROSS-PLATFORM TEST DEBUG ===")
    
    for client, server in combinations:
        print(f"\n🔍 Testing {client} → {server}...")
        
        try:
            success, details = run_cross_platform_test(client, server, base_dir)
            
            if success:
                print(f"✅ {client} → {server}: PASSED")
                passed += 1
            else:
                print(f"❌ {client} → {server}: FAILED")
                print(f"   Error: {details.get('error', 'No error details')}")
                print(f"   Phase: {details.get('phase', 'Unknown')}")
                if 'tests' in details:
                    for test_name, test_result in details['tests'].items():
                        if not test_result.get('success', True):
                            print(f"   Test '{test_name}' failed: {test_result.get('error', 'No details')}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {client} → {server}: EXCEPTION")
            print(f"   Exception: {e}")
            failed += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    return passed, failed

if __name__ == "__main__":
    os.chdir("/Users/bahram/ws/prj/Janus/tests/library_based_tests")
    passed, failed = debug_combinations()
    sys.exit(0 if failed == 0 else 1)