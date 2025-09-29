#!/usr/bin/env python3
"""
Workflow Testing Tool for Troubleshooting Wizard
Tests CI Pipeline, Release, and Code Quality workflows locally

Run this script directly, not as a pytest test:
python tools/workflow_tester.py
"""

import subprocess
import sys
import os
import json
from datetime import datetime


def run_command(cmd, description, cwd=None):
    """Run a command and return success status."""
    print(f"Running {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, 
            text=True, encoding='utf-8', cwd=cwd
        )
        print(f"[PASS] {description} passed")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {description} failed:")
        print(e.stdout)
        print(e.stderr)
        return False, e.stderr


def test_code_quality():
    """Test Code Quality workflow"""
    print("\n=== Testing Code Quality Workflow ===")
    return run_command("python tools/format_code.py", "Code Quality")[0]


def test_ci_pipeline():
    """Test CI Pipeline workflow"""
    print("\n=== Testing CI Pipeline Workflow ===")
    
    # Test dependency installation
    success, _ = run_command("pip install -e \".[dev]\"", "Dependencies Installation")
    if not success:
        return False
    
    # Test pytest
    success, _ = run_command("python -m pytest tests/ -v", "Unit Tests")
    if not success:
        return False
    
    # Test health checks
    health_cmd = (
        "python -c \"from src.logging_config import setup_logging; "
        "setup_logging(); from src.health_check import run_health_checks; "
        "exit(0 if run_health_checks() else 1)\""
    )
    success, _ = run_command(health_cmd, "Health Checks")
    if not success:
        return False
    
    # Test package build
    success, _ = run_command("python -m build", "Package Build")
    return success


def test_release():
    """Test Release workflow"""
    print("\n=== Testing Release Workflow ===")
    
    # Test executable build
    success, _ = run_command("powershell -File tools/build.ps1", "Executable Build")
    if not success:
        return False
    
    # Check if exe exists
    if os.path.exists("dist/run.exe"):
        print("[PASS] Executable created successfully")
        return True
    else:
        print("[FAIL] Executable not found")
        return False


def main():
    """Run all workflow tests"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    print(f"Testing workflows in: {project_root}")
    
    results = {
        "Code Quality": test_code_quality(),
        "CI Pipeline": test_ci_pipeline(), 
        "Release": test_release()
    }
    
    print("\n" + "="*50)
    print("WORKFLOW TEST RESULTS")
    print("="*50)
    
    all_passed = True
    for workflow, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{workflow:15} [{status}]")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All workflows ready for GitHub!")
        return 0
    else:
        print("\n❌ Some workflows need fixes before pushing")
        return 1


if __name__ == "__main__":
    sys.exit(main())