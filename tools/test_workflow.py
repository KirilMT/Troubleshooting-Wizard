#!/usr/bin/env python3
"""
Workflow Testing Tool for Troubleshooting Wizard
Tests CI Pipeline, Release, and Code Quality workflows locally

Run with pytest:
pytest tools/test_workflow.py -v
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
    success, _ = run_command("python tools/format_code.py", "Code Quality")
    assert success, "Code Quality workflow failed"


def test_ci_pipeline():
    """Test CI Pipeline workflow"""
    print("\n=== Testing CI Pipeline Workflow ===")
    
    # Test dependency installation
    success, _ = run_command("pip install -e \".[dev]\"", "Dependencies Installation")
    assert success, "Dependencies installation failed"
    
    # Test pytest (stable core tests)
    success, _ = run_command("python -m pytest tests/test_core.py tests/test_database_manager.py tests/test_ui_components.py -v", "Unit Tests")
    assert success, "Unit tests failed"
    
    # Test health checks
    health_cmd = (
        "python -c \"from src.logging_config import setup_logging; "
        "setup_logging(); from src.health_check import run_health_checks; "
        "exit(0 if run_health_checks() else 1)\""
    )
    success, _ = run_command(health_cmd, "Health Checks")
    assert success, "Health checks failed"
    
    # Test package build
    success, _ = run_command("python -m build", "Package Build")
    assert success, "Package build failed"


def test_release():
    """Test Release workflow"""
    print("\n=== Testing Release Workflow ===")
    
    # Test executable build
    success, _ = run_command("powershell -File tools/build.ps1", "Executable Build")
    assert success, "Executable build failed"
    
    # Check if exe exists
    assert os.path.exists("dist/run.exe"), "Executable not found"


def setup_module():
    """Setup for pytest - change to project root"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    print(f"\nTesting workflows in: {project_root}")


if __name__ == "__main__":
    # Allow running directly for backwards compatibility
    import pytest
    pytest.main([__file__, "-v"])