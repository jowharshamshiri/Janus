#!/usr/bin/env python3
"""
Comprehensive Test Runner for UnixSocketAPI
Main entry point for running all tests across all implementations
"""

import sys
import os
import argparse
from pathlib import Path

# Add python test directory to path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from comprehensive_test_suite import ComprehensiveTestSuite, TestCategory

def main():
    """Main entry point for comprehensive testing"""
    parser = argparse.ArgumentParser(
        description="UnixSocketAPI Comprehensive Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all basic tests (build, unit, cross-platform)
  python tests/run_comprehensive_tests.py
  
  # Run with performance and security tests
  python tests/run_comprehensive_tests.py --performance --security
  
  # Run only cross-platform communication tests
  python tests/run_comprehensive_tests.py --categories cross_platform
  
  # Run with verbose output
  python tests/run_comprehensive_tests.py --verbose
  
  # Test specific implementations only
  python tests/run_comprehensive_tests.py --implementations go,rust
        """
    )
    
    parser.add_argument("--config", default="tests/config/unified-test-config.json", 
                       help="Test configuration file (default: tests/config/unified-test-config.json)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    parser.add_argument("--categories", 
                       default="build,unit,cross_platform",
                       help="Test categories to run (comma-separated): build,unit,cross_platform,performance,security,stress")
    parser.add_argument("--implementations", 
                       help="Specific implementations to test (comma-separated): go,rust,swift,typescript")
    parser.add_argument("--performance", action="store_true", 
                       help="Include performance benchmarks")
    parser.add_argument("--security", action="store_true", 
                       help="Include security and conformance tests")
    parser.add_argument("--stress", action="store_true", 
                       help="Include stress testing")
    parser.add_argument("--output-dir", 
                       help="Custom output directory for logs and reports")
    
    args = parser.parse_args()
    
    # Parse categories
    category_map = {c.value: c for c in TestCategory}
    categories = set()
    
    for cat_name in args.categories.split(","):
        cat_name = cat_name.strip()
        if cat_name in category_map:
            categories.add(category_map[cat_name])
        else:
            print(f"Warning: Unknown category '{cat_name}'")
    
    # Add additional categories from flags
    if args.performance:
        categories.add(TestCategory.PERFORMANCE)
    if args.security:
        categories.add(TestCategory.SECURITY)
    if args.stress:
        categories.add(TestCategory.STRESS)
    
    # Ensure we always have build tests
    categories.add(TestCategory.BUILD)
    
    print("UnixSocketAPI Comprehensive Test Suite")
    print("=" * 50)
    print(f"Configuration: {args.config}")
    print(f"Categories: {[c.value for c in sorted(categories, key=lambda x: x.value)]}")
    if args.implementations:
        print(f"Implementations: {args.implementations}")
    print()
    
    try:
        # Create test suite
        test_suite = ComprehensiveTestSuite(
            config_path=args.config,
            verbose=args.verbose
        )
        
        # Filter implementations if specified
        if args.implementations:
            impl_filter = set(args.implementations.split(","))
            filtered_impls = {
                name: impl for name, impl in test_suite.implementations.items()
                if name in impl_filter
            }
            test_suite.implementations = filtered_impls
            print(f"Filtered to implementations: {list(filtered_impls.keys())}")
        
        # Run tests
        report = test_suite.run_all_tests(categories)
        
        # Print summary
        summary = report["summary"]
        print(f"\n{'='*60}")
        print("COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        if summary['skipped'] > 0:
            print(f"Skipped: {summary['skipped']} ⏭️")
        if summary['errors'] > 0:
            print(f"Errors: {summary['errors']} 🚨")
        if summary['timeouts'] > 0:
            print(f"Timeouts: {summary['timeouts']} ⏰")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"\nReports saved to: {test_suite.report_dir}")
        
        # Print implementation status
        print(f"\nImplementation Status:")
        for name, info in report['implementations'].items():
            status = "✅ Available" if info['build_successful'] else "❌ Failed"
            print(f"  {name} ({info['language']}): {status}")
        
        # Print category breakdown
        print(f"\nResults by Category:")
        for category, results in report['results_by_category'].items():
            passed = len([r for r in results if r['status'] == 'PASS'])
            total = len(results)
            print(f"  {category}: {passed}/{total} passed")
        
        # Show failed tests if any
        failed_tests = [r for r in report['detailed_results'] if r['status'] == 'FAIL']
        if failed_tests:
            print(f"\nFailed Tests:")
            for test in failed_tests:
                impl_info = f" ({test['implementation']}" 
                if test['target_implementation']:
                    impl_info += f" → {test['target_implementation']}"
                impl_info += ")"
                print(f"  ❌ {test['name']}{impl_info}: {test['message']}")
        
        # Exit with appropriate code
        sys.exit(0 if summary['failed'] == 0 else 1)
        
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Test suite error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()