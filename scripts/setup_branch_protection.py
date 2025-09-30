#!/usr/bin/env python3
"""
Script to set up branch protection rules for the repository.
This ensures that CI checks must pass before code can be merged to main.
"""

import subprocess
import sys
import json


def run_command(cmd, check=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode


def setup_branch_protection():
    """Set up branch protection rules for the main branch."""
    print("Setting up branch protection rules...")

    # Branch protection configuration
    protection_config = {
        "required_status_checks": {"strict": True, "contexts": ["Run Tests", "Build Package"]},
        "enforce_admins": False,
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False,
        },
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }

    # Convert to JSON string for the API call
    config_json = json.dumps(protection_config)

    # Set up branch protection using GitHub CLI
    cmd = f"gh api repos/:owner/:repo/branches/main/protection -X PUT --input -"

    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(input=config_json)

        if process.returncode == 0:
            print("✅ Branch protection rules successfully applied!")
            print("Main branch now requires:")
            print("  - CI checks to pass")
            print("  - Pull request reviews")
            print("  - No direct pushes to main")
            return True
        else:
            print(f"❌ Failed to set branch protection: {stderr}")
            return False

    except Exception as e:
        print(f"❌ Error setting up branch protection: {e}")
        return False


def verify_protection():
    """Verify that branch protection is properly configured."""
    print("\nVerifying branch protection...")

    stdout, stderr, returncode = run_command(
        "gh api repos/:owner/:repo/branches/main/protection", check=False
    )

    if returncode == 0:
        protection = json.loads(stdout)
        print("✅ Branch protection is active!")

        # Check required status checks
        if protection.get("required_status_checks"):
            contexts = protection["required_status_checks"].get("contexts", [])
            print(f"  Required CI checks: {', '.join(contexts)}")

        # Check PR requirements
        if protection.get("required_pull_request_reviews"):
            reviews = protection["required_pull_request_reviews"]
            count = reviews.get("required_approving_review_count", 0)
            print(f"  Required PR reviews: {count}")

        return True
    else:
        print("❌ Branch protection verification failed")
        return False


def main():
    """Main function to set up and verify branch protection."""
    print("🔒 Setting up CI/CD Branch Protection")
    print("=" * 40)

    # Check if GitHub CLI is available
    stdout, stderr, returncode = run_command("gh --version", check=False)
    if returncode != 0:
        print("❌ GitHub CLI (gh) is not installed or not in PATH")
        print("Please install GitHub CLI: https://cli.github.com/")
        sys.exit(1)

    # Check if user is authenticated
    stdout, stderr, returncode = run_command("gh auth status", check=False)
    if returncode != 0:
        print("❌ Not authenticated with GitHub CLI")
        print("Please run: gh auth login")
        sys.exit(1)

    # Set up branch protection
    if setup_branch_protection():
        verify_protection()
        print("\n🎉 CI/CD protection is now active!")
        print("\nNext steps:")
        print("1. All future changes must go through pull requests")
        print("2. CI checks must pass before merging")
        print("3. At least 1 review is required for PRs")
    else:
        print("\n❌ Failed to set up branch protection")
        sys.exit(1)


if __name__ == "__main__":
    main()
