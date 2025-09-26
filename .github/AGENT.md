# Gemini Code Assist Instructions

This document provides project-specific context and instructions for Gemini Code Assist.

## Project Overview

This project, Troubleshooting-Wizard, is a Python-based GUI application for industrial equipment troubleshooting and error code management. It uses `tkinter` for the user interface and `SQLite` to store data extracted from PDF manuals. The application is highly configurable through a `data.json` file, allowing users to add new technologies and resources easily.

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
│   ├── AGENT.md            # This file
│   ├── CODEOWNERS          # Code ownership information
│   ├── CONTRIBUTING.md     # Contribution guidelines
│   ├── copilot-instructions.md  # Copilot configuration
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
├── tools/                  # Development tools and scripts
├── .gitignore              # Git ignore rules
├── .pre-commit-config.yaml # Pre-commit hooks
├── CHANGELOG.md            # Version history
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

## Quick Test Guide

1.  **Run the application**: `python src/main.py`
2.  **Navigate the UI**: Select a technology and choose a task.
3.  **Test PDF Processing**: `python src/process_pdf.py --pdf-path "path/to/manual.pdf" ...`

## Interaction & Workflow

When you ask me to work on an issue, I will adhere to the following process:

1.  **Follow the Workflow:** I will first consult the `GIT_WORKFLOW.md` file to understand the prescribed development workflow.
2.  **Use Tools Proactively**: I will use my available tools to get information about the project before asking you for details.
3.  **Command Execution Protocol:** If terminal commands are required, I will provide them and wait for confirmation before proceeding.
4.  **Issue and Sub-Tasks Prioritization:** I will address issues and their sub-tasks sequentially, providing a plan and asking for your approval before making changes.
