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
    total_steps = 3

    # Install pre-commit
    if run_command("pip install pre-commit", "Pre-commit package"):
        success_count += 1

    # Install pre-commit hooks
    if run_command("pre-commit install", "Pre-commit hooks"):
        success_count += 1

    # Test the automation
    if run_command("python tools/format_code.py", "Code quality automation"):
        success_count += 1

    print(f"\n🎉 Setup complete! ({success_count}/{total_steps} steps successful)")

    if success_count == total_steps:
        print("\n✨ Your automated development workflow is ready!")
        print("\n📋 Quick Reference:")
        print("   • During development: python tools/format_code.py")
        print("   • Before pushing: python tools/test_workflow.py")
        print("   • For releases: python tools/release_manager.py patch --changes '...'")
        print("   • Pre-commit hooks: Automatically run on git commit")
        return 0
    else:
        print("\n⚠️  Some setup steps failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
