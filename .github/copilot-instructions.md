# AI Assistant Instructions for Industrial Troubleshooting Application

This document provides instructions for an AI assistant to help it provide the best possible assistance for this project.

## Project Overview

This project is a Python-based GUI application for industrial equipment troubleshooting and error code management. It centralizes access to error codes, manuals, and troubleshooting resources for various manufacturing technologies. The application uses a configuration-driven approach and supports extensibility for new technologies.

## Core Architectural Context

- The application is built with Python (PEP 8 style, class-based OOP preferred).
- The GUI uses tkinter.
- Error code tables are extracted from PDF manuals and stored in an SQLite database.
- Configuration is managed via JSON files (`example_data.json` as template, `data.json` for local settings).
- Media files (images, screenshots) are stored in the `media/` directory.

## Key Files

- **src/main.py**: Main GUI application entry point.
- **src/process_pdf.py**: Utility for extracting error code tables from PDF manuals.
- **src/example_data.json**: Configuration template (committed).
- **src/data.json**: Local configuration (user-created, not committed).
- **src/errorCodesTechnologies.db**: SQLite database for error codes.
- **media/**: Images and resources (example files committed, real files not committed).
- **requirements.txt**: Python dependencies.
- **README.md**: Project documentation.
- **LICENSE**: MIT License.

## Key Features

- Centralized error code management for multiple industrial technologies.
- PDF/manual extraction and database integration for error codes.
- Extensible configuration for adding new technologies and resources.
- Media support for images/screenshots linked to error codes.
- Secure handling of sensitive configuration and media files.
- User-friendly GUI for searching and troubleshooting.

## Development Roadmap Highlights

- Database & Data Management: Improve PDF/manual extraction, enhance schema for new technologies, and support external API integration.
- UI/UX Enhancements: Refine GUI usability, add advanced search/filtering, and improve error code visualization.
- Feature Expansion: Add support for new equipment, error types, and troubleshooting workflows.
- Testing: Expand automated test coverage and dummy data seeding.
- Documentation: Keep all documentation up to date with new features and changes.

## GitHub Issues & Workflow

- If working on a GitHub issue, you must rely on the provided issue description (external sites are inaccessible).
- Follow the workflow described in project documentation (or GIT_WORKFLOW.md if present).
- Announce which issue and sub-task you are working on, based on prioritization (highest to lowest).
- For issues with sub-tasks, address each sequentially and independently, seeking approval before proceeding.
- After each sub-task, provide a summary and wait for confirmation before moving on.
- Skip any already implemented issues/sub-tasks and move to the next.

## Development Guidelines

- **Python Code**:
  - Use class-based object-oriented programming for new features and refactoring.
  - Adhere to PEP 8 style guidelines.
  - Include basic error handling (try-except blocks).
  - Add docstrings for all new classes and methods.
  - Avoid print statements or temporary debugging logs in final code.
- **Configuration**:
  - Never commit `src/data.json` or real media files.
  - Update `src/example_data.json` when adding new technologies or features.
  - Use relative paths for media files in configuration.
  - Use example URLs in `example_data.json` (e.g., `https://example.com/path/to/file.pdf`).
- **Database**:
  - Use SQLite for storing error codes and extracted data.
  - Ensure database schema changes are documented and robust.
- **Documentation**:
  - Update `README.md`, `copilot-instructions.md`, and any other relevant files to reflect all changes.
  - Keep configuration examples generic and non-sensitive.

## Security & Data Protection

- Real configuration and media files are automatically ignored by git.
- Only example placeholders are committed.
- Sensitive data (URLs, credentials, images) stays local.

## Technologies

- Programming Language: Python 3.7+
- GUI: tkinter
- Database: SQLite
- PDF Processing: (e.g., PyPDF2, tabula-py, or similar)
- Dependencies: See `requirements.txt`

## Project Structure

```
├── src/
│   ├── main.py
│   ├── process_pdf.py
│   ├── example_data.json
│   ├── data.json
│   └── errorCodesTechnologies.db
├── media/
│   ├── README.md
│   ├── example_*.png
│   └── [your_files]
├── build/
├── requirements.txt
├── .gitignore
├── LICENSE
├── README.md
└── copilot-instructions.md
```

## Documentation Update Requirement

- Before committing and pushing, update documentation files (README.md, copilot-instructions.md, and any other relevant files) to reflect all changes.
- Ensure configuration examples remain generic and non-sensitive.

## How to Interact with Me

- Be proactive: I will scan the project to understand its structure and technologies before making changes.
- Use available tools: I will gather information before asking for clarification.
- Ask for clarification: If unsure, I will request more details.
- Follow modern development practices, but prioritize consistency with your code and style.
- Documentation Update Requirement: I will update documentation files before committing and pushing changes.

## Working on Issues

- I will follow the workflow described in project documentation.
- I will announce which issue and sub-task I am working on.
- I will provide a plan for each sub-task and wait for your approval before making changes.
- I will only proceed to the next sub-task after the current one is fully resolved.
- After completing a sub-task, I will provide a summary of the changes and wait for your confirmation to proceed.

## SEW Error Code Extraction Workflow

- The PDF extraction utility (`src/process_pdf.py`) now supports a `--sew-mode` CLI option for SEW Drive Systems.
- When enabled, SEW error codes (fault code, suberror code, description) are extracted from PDF tables and stored in the `sew_error_codes` table in `src/errorCodesTechnologies.db`.
- The table schema is:
  - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
  - `fault_code` (TEXT)
  - `suberror_code` (TEXT)
  - `description` (TEXT)
- This workflow is robust to SEW's complex error code numbering and description formats.
- Update `example_data.json` to add SEW configuration examples for future extensibility.
