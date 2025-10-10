#!/usr/bin/env python3
"""
Automated Release Manager for Troubleshooting Wizard
Handles version bumping, changelog updates, and git tagging
"""

import re
import sys
import os
import subprocess
from datetime import datetime
import argparse


class ReleaseManager:
    def __init__(self, project_root):
        self.project_root = project_root
        self.pyproject_path = os.path.join(project_root, "pyproject.toml")
        self.readme_path = os.path.join(project_root, "README.md")
        self.changelog_path = os.path.join(project_root, "CHANGELOG.md")

    def get_current_version(self):
        """Get current version from pyproject.toml"""
        with open(self.pyproject_path, "r") as f:
            content = f.read()

        match = re.search(r'version = "([^"]+)"', content)
        if match:
            return match.group(1)
        raise ValueError("Version not found in pyproject.toml")

    def bump_version(self, version_type):
        """Bump version (patch, minor, major)"""
        current = self.get_current_version()
        major, minor, patch = map(int, current.split("."))

        if version_type == "patch":
            patch += 1
        elif version_type == "minor":
            minor += 1
            patch = 0
        elif version_type == "major":
            major += 1
            minor = 0
            patch = 0
        else:
            raise ValueError("Version type must be: patch, minor, or major")

        return f"{major}.{minor}.{patch}"

    def update_pyproject_version(self, new_version):
        """Update version in pyproject.toml"""
        with open(self.pyproject_path, "r") as f:
            content = f.read()

        content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)

        with open(self.pyproject_path, "w") as f:
            f.write(content)
        print(f"Updated pyproject.toml to version {new_version}")

    def update_readme_version(self, new_version):
        """Update version in README.md"""
        current_version = self.get_current_version()

        with open(self.readme_path, "r") as f:
            content = f.read()

        # Update version line at bottom of README
        content = re.sub(r"\*\*Version: [^*]+\*\*", f"**Version: {new_version}**", content)

        with open(self.readme_path, "w") as f:
            f.write(content)
        print(f"Updated README.md: {current_version} -> {new_version}")

    def update_changelog(self, new_version, changes):
        """Update CHANGELOG.md with new version"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        current_version = self.get_current_version()

        with open(self.changelog_path, "r") as f:
            content = f.read()

        # Add new entry after the header, before existing entries
        header_pattern = r"(# Changelog.*?\n\n.*?\n\n)"
        new_entry = f"## [{new_version}] - {date_str}\n{changes}\n\n"

        if re.search(header_pattern, content, re.DOTALL):
            content = re.sub(header_pattern, f"\\1{new_entry}", content, count=1, flags=re.DOTALL)
        else:
            # Fallback: add after first ## entry
            content = re.sub(r"(## \[.*?\])", f"{new_entry}\\1", content, count=1)

        with open(self.changelog_path, "w") as f:
            f.write(content)
        print(f"Updated CHANGELOG.md: {current_version} -> {new_version}")

    def create_git_tag(self, version):
        """Create and push git tag"""
        tag_name = f"v{version}"

        # Add all changes
        subprocess.run(["git", "add", "."], check=True)

        # Commit changes
        commit_msg = f"Release version {version}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)

        # Create tag
        subprocess.run(["git", "tag", tag_name], check=True)

        print(f"Created git tag: {tag_name}")
        print(f"To push: git push origin main && git push origin {tag_name}")

        return tag_name

    def release(self, version_type, changes_text):
        """Perform complete release process"""
        print(f"Starting {version_type} release...")

        current_version = self.get_current_version()
        new_version = self.bump_version(version_type)

        print(f"Bumping version: {current_version} -> {new_version}")

        # Update all files
        self.update_pyproject_version(new_version)
        self.update_readme_version(new_version)
        self.update_changelog(new_version, changes_text)

        # Create git tag
        tag_name = self.create_git_tag(new_version)

        print(f"\n✅ Release {new_version} prepared!")
        print(f"📋 Next steps:")
        print(f"   1. Review changes: git diff HEAD~1")
        print(f"   2. Push to trigger release: git push origin main && git push origin {tag_name}")

        return new_version


def main():
    parser = argparse.ArgumentParser(description="Automated Release Manager")
    parser.add_argument(
        "version_type", nargs="?", choices=["patch", "minor", "major"], help="Type of version bump"
    )
    parser.add_argument("--changes", help="Description of changes for changelog")
    parser.add_argument("--auto-push", action="store_true", help="Automatically push to GitHub")

    args = parser.parse_args()

    # Interactive mode if no arguments provided
    if not args.version_type:
        print("🚀 Interactive Release Manager")
        print("==============================")

        # Get version type
        print("\nSelect version bump type:")
        print("1. patch (1.2.0 -> 1.2.1) - Bug fixes")
        print("2. minor (1.2.0 -> 1.3.0) - New features")
        print("3. major (1.2.0 -> 2.0.0) - Breaking changes")

        while True:
            choice = input("\nEnter choice (1-3): ").strip()
            if choice == "1":
                args.version_type = "patch"
                break
            elif choice == "2":
                args.version_type = "minor"
                break
            elif choice == "3":
                args.version_type = "major"
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

    if not args.changes:
        args.changes = input("\nEnter description of changes: ").strip()
        if not args.changes:
            args.changes = f"Release version with {args.version_type} updates"

    if not args.auto_push:
        push_choice = input("\nAuto-push to GitHub? (y/N): ").strip().lower()
        args.auto_push = push_choice in ["y", "yes"]

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    manager = ReleaseManager(project_root)
    new_version = manager.release(args.version_type, args.changes)

    if args.auto_push:
        tag_name = f"v{new_version}"
        subprocess.run(["git", "push", "origin", "main"], check=True)
        subprocess.run(["git", "push", "origin", tag_name], check=True)
        print(f"🚀 Pushed release {new_version} to GitHub!")


if __name__ == "__main__":
    main()
