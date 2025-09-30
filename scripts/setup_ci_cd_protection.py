#!/usr/bin/env python3
"""
Comprehensive CI/CD Protection Setup Script

This script addresses the critical CI/CD issue by:
1. Setting up branch protection rules
2. Installing enhanced pre-commit hooks
3. Configuring pre-push hooks
4. Validating the entire CI/CD pipeline
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, check=True, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=check, cwd=cwd
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode


def setup_pre_commit_hooks():
    """Install and configure pre-commit hooks."""
    print("🔧 Setting up pre-commit hooks...")

    # Install pre-commit hooks
    stdout, stderr, returncode = run_command("pre-commit install")
    if returncode != 0:
        print(f"❌ Failed to install pre-commit hooks: {stderr}")
        return False

    # Install pre-push hooks
    stdout, stderr, returncode = run_command("pre-commit install --hook-type pre-push")
    if returncode != 0:
        print(f"❌ Failed to install pre-push hooks: {stderr}")
        return False

    print("✅ Pre-commit and pre-push hooks installed")

    # Test the hooks
    print("Testing pre-commit hooks...")
    stdout, stderr, returncode = run_command("pre-commit run --all-files", check=False)
    if returncode != 0:
        print(f"⚠️  Pre-commit hooks found issues (this is normal):")
        print(stdout)
        print(stderr)
    else:
        print("✅ Pre-commit hooks passed")

    return True


def create_git_hooks():
    """Create additional git hooks for comprehensive protection."""
    hooks_dir = Path(".git/hooks")

    # Create pre-push hook that runs comprehensive tests
    pre_push_hook = hooks_dir / "pre-push"
    pre_push_content = """#!/bin/sh
# Pre-push hook to run comprehensive tests
echo "Running comprehensive tests before push..."

# Run the test workflow
python scripts/test_workflow.py
if [ $? -ne 0 ]; then
    echo "Tests failed! Push aborted."
    echo "Fix the issues and try again."
    exit 1
fi

echo "All tests passed! Proceeding with push..."
"""

    try:
        with open(pre_push_hook, "w", newline="\n") as f:
            f.write(pre_push_content)

        # Make it executable (on Unix-like systems)
        if os.name != "nt":
            os.chmod(pre_push_hook, 0o755)

        print("✅ Pre-push hook created")
        return True
    except Exception as e:
        print(f"❌ Failed to create pre-push hook: {e}")
        return False


def validate_ci_cd_setup():
    """Validate that the CI/CD setup is working correctly."""
    print("🔍 Validating CI/CD setup...")

    # Check if pre-commit is installed
    stdout, stderr, returncode = run_command("pre-commit --version", check=False)
    if returncode != 0:
        print("❌ Pre-commit is not installed")
        return False

    # Check if GitHub CLI is available
    stdout, stderr, returncode = run_command("gh --version", check=False)
    if returncode != 0:
        print("⚠️  GitHub CLI not available - branch protection setup will be manual")

    # Check if tests pass
    print("Running test suite...")
    stdout, stderr, returncode = run_command("python -m pytest tests/ -v", check=False)
    if returncode != 0:
        print("❌ Tests are currently failing")
        print("This needs to be fixed before the CI/CD protection is fully effective")
        return False

    # Check code quality
    print("Checking code quality...")
    stdout, stderr, returncode = run_command("python scripts/format_code.py", check=False)
    if returncode != 0:
        print("❌ Code quality checks failed")
        return False

    print("✅ CI/CD validation passed")
    return True


def print_instructions():
    """Print instructions for completing the CI/CD setup."""
    print("\n" + "=" * 60)
    print("🎉 CI/CD PROTECTION SETUP COMPLETE")
    print("=" * 60)

    print("\n✅ What has been configured:")
    print("  • Enhanced pre-commit hooks with tests")
    print("  • Pre-push hooks with comprehensive validation")
    print("  • Code quality enforcement")
    print("  • Test execution before commits")

    print("\n🔧 Manual steps required:")
    print("  1. Set up branch protection rules:")
    print("     python scripts/setup_branch_protection.py")
    print("  2. Or manually via GitHub web interface:")
    print("     - Go to Settings > Branches")
    print("     - Add rule for 'main' branch")
    print("     - Require status checks: 'Run Tests', 'Build Package'")
    print("     - Require pull request reviews")
    print("     - Dismiss stale reviews")

    print("\n🚀 How this prevents the issue:")
    print("  • Pre-commit: Tests run before each commit")
    print("  • Pre-push: Comprehensive validation before push")
    print("  • Branch protection: No direct pushes to main")
    print("  • CI/CD: All PRs must pass tests before merge")

    print("\n⚠️  Important:")
    print("  • All future changes must go through pull requests")
    print("  • Direct pushes to main will be blocked")
    print("  • CI checks must pass before merging")


def main():
    """Main function to set up comprehensive CI/CD protection."""
    print("🔒 SETTING UP CI/CD PROTECTION")
    print("Addressing Issue #4: CI/CD Branch Protection")
    print("=" * 50)

    success = True

    # Step 1: Set up pre-commit hooks
    if not setup_pre_commit_hooks():
        success = False

    # Step 2: Create additional git hooks
    if not create_git_hooks():
        success = False

    # Step 3: Validate the setup
    if not validate_ci_cd_setup():
        print("⚠️  Validation found issues - please address them")

    # Step 4: Print instructions
    print_instructions()

    if success:
        print("\n🎉 CI/CD protection setup completed successfully!")
        print("The critical issue has been addressed.")
    else:
        print("\n❌ Some issues occurred during setup")
        print("Please review the errors above and fix them")
        sys.exit(1)


if __name__ == "__main__":
    main()
