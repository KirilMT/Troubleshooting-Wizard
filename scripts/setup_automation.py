#!/usr/bin/env python3
"""
Setup Automation for Troubleshooting Wizard
Configures pre-commit hooks and development automation
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"Setting up {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} setup complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} setup failed:")
        print(e.stderr)
        return False


def main():
    """Set up automated development workflow."""
    print("🚀 Setting up Troubleshooting Wizard Development Automation\n")

    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    success_count = 0
    total_steps = 5

    # Install all requirements (including pre-commit)
    if run_command("pip install -r requirements.txt", "Project dependencies"):
        success_count += 1

    # Install pre-commit hooks
    if run_command("pre-commit install", "Pre-commit hooks"):
        success_count += 1

    # Migrate pre-commit config if needed
    if run_command("pre-commit migrate-config", "Pre-commit configuration migration"):
        success_count += 1

    # Test pre-commit hooks
    if run_command("pre-commit run --all-files", "Pre-commit hook validation"):
        success_count += 1

    # Test the code quality automation
    if run_command("python scripts/format_code.py", "Code quality automation"):
        success_count += 1

    print(f"\n🎉 Setup complete! ({success_count}/{total_steps} steps successful)")

    if success_count == total_steps:
        print("\n✨ Your automated development workflow is ready!")
        print("📋 What's been set up:")
        print("   • All project dependencies installed")
        print("   • Pre-commit hooks installed and configured")
        print("   • Code formatting and linting automation")
        print("   • Git hooks for automatic code quality checks")
        print("\n🔧 Next time, just run: python scripts/setup_automation.py")
    else:
        print(f"\n⚠️  Some steps failed. Please check the errors above.")


if __name__ == "__main__":
    main()
