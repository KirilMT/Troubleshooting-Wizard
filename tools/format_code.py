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
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, encoding='utf-8')
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
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    # Use virtual environment tools explicitly to avoid conflicts
    venv_python = os.path.join(project_root, ".venv", "Scripts", "python.exe")
    if os.path.exists(venv_python):
        black_cmd = f'"{venv_python}" -m black --check --line-length=100 src/ run.py'
        flake8_cmd = f'"{venv_python}" -m flake8 src/ run.py --max-line-length=100 --ignore=E203,W503,E231,E241,E202'
    else:
        # Fallback to system commands
        black_cmd = "black --check --line-length=100 src/ run.py"
        flake8_cmd = "flake8 src/ run.py --max-line-length=100 --ignore=E203,W503,E231,E241,E202"
    
    # Add import sorting check
    if os.path.exists(venv_python):
        isort_cmd = f'"{venv_python}" -m isort --check-only --diff src/ run.py'
    else:
        isort_cmd = "python -m isort --check-only --diff src/ run.py"
    
    checks = [
        (black_cmd, "Code formatting (black)"),
        (flake8_cmd, "Code linting (flake8)"),
        (isort_cmd, "Import sorting (isort)")
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