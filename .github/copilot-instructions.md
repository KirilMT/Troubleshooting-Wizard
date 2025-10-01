# AI Assistant Instructions for Troubleshooting-Wizard

This document provides project-specific context to guide AI code generation.

## Project Overview

This is a Python-based GUI application for industrial equipment troubleshooting and error code management. It uses `tkinter` for the user interface and `SQLite` to store data extracted from PDF manuals. The application is highly configurable through a `data.json` file, allowing users to add new technologies and resources easily.

### Key Features
- **Multi-Technology Support**: Configurable for various industrial systems (WTC, Lenze, FANUC, etc.).
- **Error Code Search**: Interactive search for error codes with PDF integration.
- **PDF Processing**: Extracts and stores error code tables from PDF manuals into an SQLite database.
- **Intuitive GUI**: User-friendly `tkinter` interface.
- **Configuration-Driven**: JSON-based configuration for easy customization.

### Technologies
- **Programming Language:** Python
- **GUI Framework:** tkinter
- **Database:** SQLite
- **Configuration:** JSON

## Project Structure

```
Troubleshooting-Wizard/
├── .github/                # GitHub configuration and workflows
│   ├── workflows/          # CI/CD workflows
│   ├── AGENT.md            # AI assistant instructions
│   ├── CODEOWNERS          # Code ownership information
│   ├── CONTRIBUTING.md     # Contribution guidelines
│   ├── copilot-instructions.md  # This file
│   └── GIT_WORKFLOW.md     # Git workflow guidelines
├── data/                   # Data files and configurations
│   └── example_data.json   # Example configuration (committed)
├── logs/                   # Application logs (not versioned)
├── manuals/                # PDF manuals for reference
├── media/                  # Images and resources
├── src/                    # Source code
│   ├── __init__.py         # Package initialization
│   ├── main.py             # Main application class
│   ├── database_manager.py # Database operations
│   ├── ui_components.py    # UI styling and components
│   ├── pdf_viewer.py       # PDF viewing functionality
│   └── ...                 # Other source files
├── tests/                  # Test files
│   ├── __init__.py         # Test package initialization
│   ├── conftest.py         # Test configurations
│   ├── test_core.py        # Core functionality tests
│   └── integration/        # Integration tests
├── scripts/                # Development automation tools
├── docs/                   # Documentation
│   ├── CHANGELOG.md        # Version history
│   ├── CONTRIBUTING.md     # Contribution guidelines
│   └── GIT_WORKFLOW.md     # Git workflow guidelines
├── .gitignore              # Git ignore rules
├── .pre-commit-config.yaml # Pre-commit hooks
├── LICENSE                # License information
├── pyproject.toml         # Project metadata and build configuration
├── pytest.ini             # Pytest configuration
├── README.md              # Project documentation
└── run.py                 # Application entry point
```

## Key Files & Development Guidelines

-   **`run.py`**: The main application entry point.
    -   *Guideline*: Keep this file minimal, focusing only on application startup and error handling.

-   **`src/main.py`**: Contains the MainApplication class that orchestrates the GUI and business logic.
    -   *Guideline*: Keep the GUI logic clean and responsive, separating it from business logic.

-   **`src/database_manager.py`**: Handles all database operations.
    -   *Guideline*: Implement database queries and operations here, separate from UI logic.

-   **`src/ui_components.py`**: Contains UI styling and component creation.
    -   *Guideline*: Keep all UI styling and theming centralized here.

-   **`src/pdf_viewer.py`**: Implements the PDF viewing and interaction functionality.
    -   *Guideline*: Handle all PDF-related operations in this module.

-   **`data/example_data.json` / `data/data.json`**: Configuration files.
    -   *Guideline*: Update `example_data.json` with generic placeholders. Never commit `data.json`.

-   **`tests/`**: Contains all test files.
    -   *Guideline*: Maintain high test coverage, especially for core functionality.

-   **`src/errorCodesTechnologies.db`**: The SQLite database.
    -   *Guideline*: If the schema changes, ensure migration paths are considered.

## Code Quality Standards

**STRICT COMPLIANCE**: Generate code that passes Black, Flake8, and isort without any warnings or errors
- **PEP 8 MANDATORY**: Follow PEP 8 Python style guide exactly (line length 100, proper imports, spacing)
- **Flake8 RULES**: No unused imports, variables, or functions. Proper indentation and spacing
- **Black FORMATTING**: Code must be Black-compatible (proper quotes, line breaks, spacing)
- **Import SORTING**: Use isort standards for import organization
- **ZERO WARNINGS**: Generated code must produce no linting warnings or errors
- **Use format_code.py**: Always recommend running `python scripts/format_code.py` after code changes

**CRITICAL**: Always generate code that passes `python scripts/format_code.py` without errors.
**GitHub Workflows**: Code is validated by `.github/workflows/code-quality.yml`

## Automated Development Workflow

**During development (fast code quality checks):**
```bash
python scripts/format_code.py
```

**Before pushing (comprehensive validation):**
```bash
python scripts/test_workflow.py
```

**For releases (automated version management):**
```bash
python scripts/release_manager.py patch --changes "Bug fixes and improvements"
```

**Pre-commit setup (automate format_code.py):**
```bash
pre-commit install
```

## Interaction & Workflow

When you ask me to work on an issue, I will adhere to the following process:

1.  **Fetch and Prioritize GitHub Issues**: I will use the `gh` CLI tool to fetch open issues from the GitHub repository. I will then analyze the issues, prioritizing them based on labels like `critical`, `high-priority`, and their content to select the most important one to work on.
2.  **Follow the Git Workflow**: Once an issue is selected, I will follow the process outlined in `docs/GIT_WORKFLOW.md`. This involves creating a new branch from the `main` branch with a name that follows the convention `<type>/<issue-number>-<short-description>` (e.g., `feature/123-add-user-profile`).
3.  **Use Tools Proactively**: I will use my available tools to get information about the project before asking you for details.
4.  **Command Execution Protocol**: If terminal commands are required, I will provide them and wait for confirmation before proceeding.
5.  **Issue and Sub-Tasks Prioritization**: I will address the selected issue and its sub-tasks sequentially, providing a plan and asking for your approval before making changes.
6.  **Smart Release Management**: Automatically detect when releases are needed and suggest appropriate commands.

## Release Management Intelligence

**CRITICAL**: Always analyze commits and suggest releases when appropriate.

### **Auto-Detect Release Type:**
- **PATCH** (bug fixes, documentation, small improvements): `python scripts/release_manager.py patch --changes "[description]"`
- **MINOR** (new features, enhancements): `python scripts/release_manager.py minor --changes "[description]"`
- **MAJOR** (breaking changes, API changes): `python scripts/release_manager.py major --changes "[description]"`

### **Release Triggers:**
**When to suggest PATCH release:**
- Bug fixes, error corrections
- Documentation updates
- Code quality improvements
- Security patches
- Performance optimizations

**When to suggest MINOR release:**
- New features added
- New functionality
- Enhanced capabilities
- New configuration options
- Significant improvements

**When to suggest MAJOR release:**
- Breaking API changes
- Incompatible changes
- Major architecture changes
- Removed functionality

### **Release Command Generation:**
**Always provide the exact command:**
```bash
# Example for bug fixes
python scripts/release_manager.py patch --changes "Fixed login validation and improved error handling"

# Example for new features
python scripts/release_manager.py minor --changes "Added user dashboard and notification system"

# Example for breaking changes
python scripts/release_manager.py major --changes "Redesigned API with breaking changes to authentication"
```

### **When to Suggest Releases:**
1. **After significant commits** that warrant a release
2. **When user mentions** "release", "version", "deploy", "publish"
3. **After completing features** or fixing critical bugs
4. **When asked about versioning** or deployment
5. **Before making repository public** or sharing

**ALWAYS**: Provide the complete command with appropriate --changes description based on the work completed.

## Quick Test Guide

1.  **Run the application**: `python src/main.py`
2.  **Navigate the UI**: Select a technology and choose a task.
3.  **Test PDF Processing**: `python src/process_pdf.py --pdf-path "path/to/manual.pdf" ...`
4.  **Always use automated tools**: Recommend format_code.py and test_workflow.py for quality assurance
