#!/usr/bin/env python3
"""
Unified Environment Setup Script for Troubleshooting Wizard

This script configures the complete development environment, including:
1.  Local development automation (pre-commit hooks)
2.  CI/CD validation (testing and code quality)
3.  GitHub branch protection for the 'main' branch
"""

import subprocess
import sys
import os
import json


def run_command(cmd, check=True, cwd=None):
    """Run a command and return the result, handling encoding issues."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check,
            cwd=cwd,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        # This allows us to capture output even when the command fails
        return e.stdout.strip(), e.stderr.strip(), e.returncode


def setup_local_automation():
    """Install and configure pre-commit hooks."""
    print("🔧 1. Setting up Local Development Automation...")

    # Install pre-commit hooks
    print("   - Installing pre-commit and pre-push hooks...")
    stdout, stderr, returncode = run_command("python -m pre_commit install")
    if returncode != 0:
        print(f"   ❌ Failed to install pre-commit hooks: {stderr}")
        return False

    stdout, stderr, returncode = run_command("python -m pre_commit install --hook-type pre-push")
    if returncode != 0:
        print(f"   ❌ Failed to install pre-push hooks: {stderr}")
        return False
    print("   ✅ Hooks installed successfully.")

    # Test the hooks. It's normal for the first run to 'fail' if it fixes files.
    print("   - Running pre-commit checks...")
    stdout, stderr, returncode = run_command("python -m pre_commit run --all-files", check=False)

    if returncode != 0:
        print("   ⚠️  Pre-commit found issues and may have fixed files. Running again to confirm.")
        stdout, stderr, returncode = run_command(
            "python -m pre_commit run --all-files", check=False
        )
        if returncode != 0:
            print("   ❌ Pre-commit hooks failed on the second run. Please fix the issues below:")
            print(stdout)
            print(stderr)
            return False

    print("   ✅ Pre-commit checks passed.")
    return True


def validate_environment():
    """Validate the environment by running tests and quality checks."""
    print("\n🔍 2. Validating Environment...")

    # Check if pre-commit is installed
    stdout, stderr, returncode = run_command("python -m pre_commit --version", check=False)
    if returncode != 0:
        print("   ❌ Pre-commit is not installed. Please run 'pip install -r requirements.txt'")
        return False

    # Run the test suite
    print("   - Running test suite...")
    stdout, stderr, returncode = run_command("python -m pytest tests/ -v", check=False)
    if returncode != 0:
        print("   ❌ Tests are failing. This must be fixed to ensure CI/CD integrity.")
        print(stdout)
        print(stderr)
        return False
    print("   ✅ All tests passed.")

    # Run code quality checks
    print("   - Checking code quality...")
    stdout, stderr, returncode = run_command("python scripts/format_code.py", check=False)
    if returncode != 0:
        print("   ❌ Code quality checks failed.")
        return False
    print("   ✅ Code quality checks passed.")
    return True


def setup_branch_protection():
    """Set up and verify branch protection rules on GitHub."""
    print("\n🔒 3. Setting up GitHub Branch Protection...")

    # Check for GitHub CLI
    if run_command("gh --version", check=False)[2] != 0:
        print("   ⚠️  GitHub CLI (gh) not found. Skipping branch protection.")
        print("      Please install it and run this script again, or set up rules manually.")
        return True  # Return True to not fail the whole script

    # Check for authentication
    if run_command("gh auth status", check=False)[2] != 0:
        print("   ❌ Not authenticated with GitHub CLI. Please run 'gh auth login'.")
        return False

    # Apply branch protection
    print("   - Applying branch protection rules for 'main' branch...")
    protection_config = {
        "required_status_checks": {"strict": True, "contexts": ["Run Tests", "Build Package"]},
        "enforce_admins": False,
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "dismiss_stale_reviews": True,
        },
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }
    config_json = json.dumps(protection_config)
    cmd = "gh api repos/:owner/:repo/branches/main/protection -X PUT --input -"

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout, stderr = process.communicate(input=config_json)

    if process.returncode != 0:
        print(f"   ❌ Failed to set branch protection: {stderr}")
        return False
    print("   ✅ Branch protection rules successfully applied.")

    # Verify the rules
    print("   - Verifying branch protection...")
    stdout, _, returncode = run_command(
        "gh api repos/:owner/:repo/branches/main/protection", check=False
    )
    if returncode == 0:
        protection = json.loads(stdout)
        contexts = protection.get("required_status_checks", {}).get("contexts", [])
        reviews = protection.get("required_pull_request_reviews", {}).get(
            "required_approving_review_count", 0
        )
        print(
            f"   ✅ Verification successful: '{', '.join(contexts)}' checks and {reviews} review(s) required."
        )
    else:
        print("   ❌ Branch protection verification failed.")
        return False

    return True


def print_summary():
    """Prints a summary of the setup process and next steps."""
    print("\n" + "=" * 60)
    print("🎉 UNIFIED ENVIRONMENT SETUP COMPLETE")
    print("=" * 60)
    print("\n✅ What has been configured:")
    print("  • Local pre-commit hooks for automated code quality.")
    print("  • Pre-push hooks to run tests before sharing code.")
    print("  • GitHub 'main' branch protection (if 'gh' was available).")
    print("\n🚀 How this improves the workflow:")
    print("  • Pre-commit: Catches issues before they are committed.")
    print("  • Pre-push: Ensures broken code isn't pushed to the repository.")
    print("  • Branch Protection: Enforces that all changes to 'main' are reviewed and tested.")
    print("\n⚠️  Important:")
    print("  • All future changes must go through Pull Requests.")
    print("  • Direct pushes to 'main' will be blocked.")
    print("  • CI checks must pass before merging.")


def main():
    """Main function to run all setup steps."""
    print("🚀 Starting Unified Environment Setup for Troubleshooting Wizard...")

    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    all_steps_passed = True

    if not setup_local_automation():
        all_steps_passed = False

    if all_steps_passed and not validate_environment():
        all_steps_passed = False

    if all_steps_passed and not setup_branch_protection():
        all_steps_passed = False

    if all_steps_passed:
        print_summary()
        print("\n✨ Your development environment is ready!")
    else:
        print("\n❌ Some setup steps failed. Please review the errors above and fix them.")
        sys.exit(1)


if __name__ == "__main__":
    main()
