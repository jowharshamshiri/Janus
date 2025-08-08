#!/usr/bin/env python3

import json
import sys

def main():
    try:
        with open('test_results.json', 'r') as f:
            results = json.load(f)
        
        print("=== FAILED TESTS ANALYSIS ===")
        
        # Check library tests
        library_tests = results.get('library_tests', {})
        for lang, result in library_tests.items():
            if result.get('status') != 'PASSED':
                print(f"❌ {lang} library test: {result.get('status')} - {result.get('error', 'No error info')}")
        
        # Check cross-platform tests  
        cross_platform = results.get('cross_platform_tests', {})
        if cross_platform:
            print(f"\n=== CROSS-PLATFORM FAILURES ===")
            total = cross_platform.get('total_tested', 0)
            passed = cross_platform.get('passed', 0)
            failed = cross_platform.get('failed', 0)
            print(f"Total: {total}, Passed: {passed}, Failed: {failed}")
            
            # Look for specific failures
            details = cross_platform.get('test_details', {})
            for test_name, test_result in details.items():
                if test_result.get('status') == 'FAILED':
                    error = test_result.get('error', 'No error details')
                    print(f"❌ {test_name}: {error[:200]}...")
        
        # Check message format tests
        message_tests = results.get('message_format_tests', {})
        if message_tests:
            print(f"\n=== MESSAGE FORMAT FAILURES ===")
            for test_name, test_result in message_tests.items():
                if test_result.get('status') != 'PASSED':
                    print(f"❌ {test_name}: {test_result.get('error', 'No error info')}")
    
    except Exception as e:
        print(f"Error reading results: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()