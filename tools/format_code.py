#!/usr/bin/env python3
"""
Code formatting and quality check script for Troubleshooting Wizard
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"Running {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"[PASS] {description} passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {description} failed:")
        print(e.stdout)
        print(e.stderr)
        return False


def main():
    """Run code formatting and quality checks."""
    # Change to project root directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    checks = [
        ("black --line-length=100 src/ run.py", "Code formatting (black)"),
        ("flake8 src/ run.py --max-line-length=100 --ignore=E203,W503,F541", "Code linting (flake8)")
    ]
    
    all_passed = True
    for cmd, description in checks:
        if not run_command(cmd, description):
            all_passed = False
    
    if all_passed:
        print("\n[SUCCESS] All code quality checks passed!")
        return 0
    else:
        print("\n[ERROR] Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())