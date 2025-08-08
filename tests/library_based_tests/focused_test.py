#!/usr/bin/env python3
"""
Run orchestrator with detailed output to identify failure patterns
"""

import subprocess
import sys

def main():
    print("Running focused cross-platform tests...")
    
    try:
        # Run orchestrator with more detailed output
        result = subprocess.run([
            "python3", "orchestrator/test_orchestrator.py"
        ], cwd="/Users/bahram/ws/prj/Janus/tests/library_based_tests", 
        capture_output=True, text=True, timeout=120)
        
        print("=== STDOUT ===")
        print(result.stdout)
        print("=== STDERR ===") 
        print(result.stderr)
        print(f"Return code: {result.returncode}")
        
        # Parse results to identify failing combinations
        lines = result.stdout.split('\n')
        
        failed_tests = []
        in_cross_platform = False
        
        for line in lines:
            if "Running Cross-Platform Communication Matrix" in line:
                in_cross_platform = True
            elif in_cross_platform:
                if "Testing:" in line and "Failed" in line:
                    failed_tests.append(line.strip())
                elif "Total Tests:" in line:
                    break
        
        if failed_tests:
            print("\n=== IDENTIFIED FAILURES ===")
            for failure in failed_tests:
                print(failure)
        else:
            print("\n=== NO SPECIFIC FAILURES IDENTIFIED ===")
            print("All tests may have passed or failure detection needs improvement")
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 2 minutes")
    except Exception as e:
        print(f"❌ Error running tests: {e}")

if __name__ == "__main__":
    main()