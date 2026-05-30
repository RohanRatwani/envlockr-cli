#!/usr/bin/env python3
"""
Run all EnvLockr unit tests
Usage: python run_tests.py
"""

import subprocess
import sys
import os

# Make emoji output safe on Windows cp1252 consoles.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass


def main():
    """Run all tests with coverage report"""
    print("=" * 60)
    print("🧪 EnvLockr Unit Tests")
    print("=" * 60)
    print()
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tests_dir = os.path.join(script_dir, "tests")
    
    # Check if tests directory exists
    if not os.path.exists(tests_dir):
        print("❌ Tests directory not found!")
        return 1
    
    # Check if pytest is available
    pytest_available = False
    try:
        import pytest  # type: ignore[import-not-found]
        pytest_available = True
    except ImportError:
        pass
    
    # Run tests
    if pytest_available:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", tests_dir, "-v", "--tb=short"],
            cwd=script_dir
        )
    else:
        # pytest not installed, fall back to unittest
        print("ℹ️  pytest not found, using unittest...")
        print()
        
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", tests_dir, "-v"],
            cwd=script_dir
        )
    
    print()
    print("=" * 60)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
