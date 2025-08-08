#!/usr/bin/env python3
"""
Run just the critical cross-platform tests using the proven implementation
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run critical tests directly"""
    
    print("🔥 Running Critical Cross-Platform Tests")
    print("=" * 50)
    
    # Run the test script that we know works
    result = subprocess.run([
        sys.executable,
        "test_go_rust_communication.py"
    ], cwd=Path(__file__).parent)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())