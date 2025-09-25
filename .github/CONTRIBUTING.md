# How to Contribute

We'd love to accept your patches and contributions to this project. There are just a few small guidelines you need to follow.

## Community Guidelines

### Our Pledge

We, as members, contributors, and leaders, pledge to make participation in our community a harassment-free experience for everyone, regardless of age, body size, visible or invisible disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming, diverse, inclusive, and healthy community.

### Our Standards

Examples of behavior that contributes to a positive environment for our community include:

*   Demonstrating empathy and kindness toward other people
*   Being respectful of differing opinions, viewpoints, and experiences
*   Giving and gracefully accepting constructive feedback
*   Accepting responsibility and apologizing to those affected by our mistakes, and learning from the experience
*   Focusing on what is best not just for us as individuals, but for the overall community

Examples of unacceptable behavior include:

*   The use of sexualized language or imagery, and sexual attention or advances of any kind
*   Trolling, insulting or derogatory comments, and personal or political attacks
*   Public or private harassment
*   Publishing others' private information, such as a physical or email address, without their explicit permission
*   Other conduct which could reasonably be considered inappropriate in a professional setting.

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the project team. All complaints will be reviewed and investigated promptly and fairly.

All community leaders are obligated to respect the privacy and security of the reporter of any incident.

---

## Contribution Process

### Setting Up Your Development Environment

To get started, you'll need to set up the project on your local machine. This will allow you to run the application and test your changes.

1.  **Follow the setup guide**: Complete the steps in the [⚙️ Setup and Installation](./../README.md#️-setup-and-installation) section of the main `README.md` file. This includes cloning the repository, creating a virtual environment, and installing the required dependencies.

2.  **Run the application**: Once your environment is set up, run the application to ensure everything is working correctly:
    ```bash
    python run.py
    ```

### Before Contributing Code

Before doing any significant work, please open an issue to propose your idea and ensure alignment. This gives everyone a chance to validate the design, helps prevent duplication of effort, and ensures that the idea fits within the project's goals.

### Sending a Pull Request

All code changes must go through a pull request. Before sending a pull request, please ensure it includes:
- Tests for any logic changes.
- A commit message that follows the conventions below.

If you are a first-time contributor, please review the [GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow).

### Commit Messages

Commit messages should follow the conventions below. Here is an example for this project:

```
feat(parser): add support for SEW PDF format

This adds a new `--sew-mode` flag to the `process_pdf.py` script to handle the specific layout of SEW Drive System manuals.

Resolves #42
```

**First Line:**
The first line is a short summary with the structure `type(scope): description`.
-   **type**: A structural element like `feat`, `fix`, `docs`, `style`, `refactor`, `test`, or `chore`.
-   **scope**: The part of the codebase affected (e.g., `parser`, `gui`, `config`).
-   **description**: A short summary written to complete the sentence "This change modifies the application to..."

**Main Content:**
The rest of the message should provide context for the change, explaining what it does and why. Write in complete sentences.

**Referencing Issues:**
To automatically close an issue when a pull request is merged, use a keyword like `Resolves #123`, `Fixes #123`, or `Closes #123` in the pull request description or commit message.

### The Review Process

- After creating a pull request, a reviewer will be assigned.
- Address any feedback by pushing additional commits to your branch. This makes it easier for reviewers to see what has changed.
- Once the pull request is approved and all checks pass, it will be squashed and merged.

### Leaving a TODO

When adding a `TODO` to the codebase, always include a link to a GitHub issue to provide context.

```python
# TODO(https://github.com/<your-org>/<your-repo>/issues/<issue-number>): Explain what needs to be done.
