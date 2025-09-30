# Professional Git Workflow Guide

This document outlines the standard process for contributing to this project. Following these steps ensures the `main` branch remains stable and all changes are properly managed.

---

### 1. Initial Setup (First Time on a New Machine)

If you are starting on a new computer or don't have the project locally, you need to clone it from GitHub.

```sh
# Clone the repository from GitHub to your local machine
git clone <repository-url>

# Navigate into the newly created project directory
cd <repository-folder>
```

---

### 2. Starting New Work (Creating a Feature Branch)

Before starting any new feature, bugfix, or improvement, always create a new branch from an up-to-date `main`.

**Step 2.1: Sync Your Local `main` Branch**

Make sure your local `main` branch has the latest changes from the remote repository.

```sh
# Switch to the main branch
git checkout main

# Pull the latest changes from the remote `main`
git pull origin main
```

**Step 2.2: Create Your New Branch**

Create a new branch with a descriptive name (e.g., `fix-login-bug`, `add-user-profiles`, `refactor-database-queries`).

```sh
# Create a new branch and switch to it in one command
# Replace `new-feature-name` with your actual branch name
git checkout -b new-feature-name
```

---

### 3. During Development (Committing and Pushing)

Now you are on your new branch and can work safely without affecting `main`.

**Step 3.0: Automated Development Workflow**

This project includes automated tools to ensure code quality and streamline development:

```sh
# During development (fast code quality checks)
python scripts/format_code.py

# Before pushing (comprehensive validation)
python scripts/test_workflow.py

# For releases (automated version management)
python scripts/release_manager.py patch --changes "Bug fixes and improvements"
```

**Step 3.1: Do Your Work and Commit Changes**

Make your code changes, then commit them with clear, descriptive messages. You can make as many commits as you need.

```sh
# Stage your changed files for the commit
git add .

# Commit the staged files with a message
git commit -m "Add a clear and concise commit message here"
```

**Step 3.2: Keep Your Branch Updated**

To prevent merge conflicts and ensure your feature branch has the latest changes from `main`, you should sync it regularly. This is especially important before creating a pull request.

```sh
# Switch to the main branch and pull the latest changes
git checkout main
git pull origin main

# Switch back to your feature branch
git checkout new-feature-name

# Merge the latest main into your feature branch
git merge main

# If there are any conflicts, resolve them now, then commit the merge.
```

**Step 3.3: Push Your Branch to the Remote**

Push your branch to the remote repository. This is required before you can open a Pull Request.

```sh
# The -u flag sets the upstream branch, so next time you can just `git push`
git push -u origin new-feature-name
```

---

### 4. Automated Development Tools

This project provides three automated tools to streamline development and ensure quality:

#### 4.1 Daily Development - Code Quality (`format_code.py`)

**Purpose:** Fast code quality checks during development
**When to use:** After making changes, before committing

```sh
python scripts/format_code.py
```

**What it does:**
- Runs Black code formatting
- Checks Flake8 linting rules
- Validates import sorting with isort
- Takes 2-3 seconds to complete

#### 4.2 Pre-Push Validation (`test_workflow.py`)

**Purpose:** Comprehensive validation before pushing to GitHub
**When to use:** Before creating pull requests or pushing to remote

```sh
python scripts/test_workflow.py
```

**What it does:**
- Validates all GitHub Actions workflows locally
- Runs complete test suite with coverage
- Tests package building and executable creation
- Ensures CI will pass on GitHub
- Takes 1-2 minutes to complete

#### 4.3 Release Management (`release_manager.py`)

**Purpose:** Automated version management and releases
**When to use:** When ready to create a new release

```sh
# Patch release (1.2.0 -> 1.2.1) - Bug fixes
python scripts/release_manager.py patch --changes "Fixed login bug and improved error handling"

# Minor release (1.2.0 -> 1.3.0) - New features
python scripts/release_manager.py minor --changes "Added user dashboard and notification system"

# Major release (1.2.0 -> 2.0.0) - Breaking changes
python scripts/release_manager.py major --changes "Redesigned API with breaking changes"

# Interactive mode (prompts for input)
python scripts/release_manager.py
```

**What it does:**
- Updates version numbers in all files
- Creates changelog entries
- Commits changes with proper tags
- Optionally pushes to GitHub for automated release

#### 4.4 Pre-commit Hook Setup (Optional)

To automatically run code quality checks before each commit:

```sh
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Now format_code.py runs automatically before each commit
```

---

### 5. Versioning

This project follows Semantic Versioning (SemVer) and uses automated release management.

**Format:** `MAJOR.MINOR.PATCH` (e.g., `1.1.0`)

-   **MAJOR (`1.x.x`):** Increment for incompatible API changes.
-   **MINOR (`x.1.x`):** Increment for new, backward-compatible features.
-   **PATCH (`x.x.1`):** Increment for backward-compatible bug fixes.

**Note:** Use `release_manager.py` for automated version management instead of manual updates.

---

### 6. Finishing Your Work (Creating a Pull Request)

Once your feature is complete and pushed to GitHub, you will create a Pull Request (PR) to merge it into the `main` branch. This is the standard way to propose changes and allow for review. For detailed guidelines on contributing, including commit message conventions and the review process, please refer to the [`CONTRIBUTING.md`](./CONTRIBUTING.md) file.

**Step 5.1: Open a Pull Request on GitHub**

1.  Go to your repository on GitHub in your web browser.
2.  You will likely see a yellow banner with your recently pushed branch and a button that says **"Compare & pull request"**. Click it.
3.  If you don't see the banner, go to the **"Pull requests"** tab and click **"New pull request"**.
4.  Set the `base` branch to `main` and the `compare` branch to your feature branch (`new-feature-name`).
5.  Give the PR a clear title (e.g., "Fixes #32: Error in search functionality") and a description of the changes.
6.  Click **"Create pull request"**.

**Step 5.2: Review and Merge the Pull Request**

On the GitHub PR page, you can see your changes, and others can review them. Once it's approved and passes any checks, you can merge it.

1.  Click the **"Merge pull request"** button on the GitHub PR page.
2.  Confirm the merge.

---

### 7. Handling Work-in-Progress (Creating a Draft Pull Request)

If your work is not yet finished but you want to get feedback, or simply want to see your changes on GitHub, you should create a **Draft Pull Request**. This signals to others that the work is still in progress.

**Why Use a Draft Pull Request?**

*   **Clear Communication:** It makes it obvious that the code is not ready for a final review or merging.
*   **Early Feedback:** You can ask for feedback on your approach before you are too far into the work.
*   **Track Your Work:** It provides a clear link between your branch and the issue you are working on.

**Step 6.1: How to Create a Draft Pull Request**

1.  Follow the same steps as opening a regular pull request (Step 5.1).
2.  On the "Open a pull request" screen, instead of clicking the "Create pull request" button, click the dropdown arrow next to it.
3.  Select **"Create draft pull request"** from the dropdown menu.
4.  In the title or description, it's a good practice to add "WIP:" (Work in Progress) and link the issue you are working on.

**Step 6.2: How to Continue Working on a Draft PR**

1.  Continue to make commits to your local branch as usual (`git commit -m "..."`).
2.  When you are ready to update the draft PR on GitHub, simply push your changes:
    ```sh
    git push
    ```
3.  Your new commits will be automatically added to the draft pull request.

**Step 6.3: Marking the PR as Ready for Review**

Once you have finished your work and the draft PR is ready for a final review, you can convert it to a regular pull request.

1.  Go to the pull request page on GitHub.
2.  Click the **"Ready for review"** button.

This will change the status of the PR and notify reviewers that it is ready to be merged.

---

### 8. Cleaning Up After Merging

After your PR is merged, the final step is to clean up your local and remote branches.

**Step 7.1: Delete the Remote Branch**

After merging on GitHub, a **"Delete branch"** button will appear. Click it to delete the remote feature branch. This keeps the repository clean.

**Step 7.2: Update Your Local Repository**

Now, update your local `main` branch with the changes you just merged on GitHub.

```sh
# Switch back to your local main branch
git checkout main

# Pull the latest changes from the remote (which includes your merged PR)
git pull origin main
```

**Step 7.3: Prune Stale Remote Branches**

Your local repository might still be tracking the remote branch you just deleted. Run the following command to clean up these stale branches.

```sh
# Fetch the latest remote state and remove any remote-tracking branches that no longer exist
git fetch --prune
```

**Step 7.4: Delete Your Local Branch**

Finally, delete the local feature branch as it is no longer needed.

```sh
# Delete the local branch
git branch -d new-feature-name
```

This completes the workflow. You are now ready to start on the next task by creating a new branch from your up-to-date `main`.
