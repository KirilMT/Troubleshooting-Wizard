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
├── src/
│   ├── main.py              # Main GUI application
│   ├── process_pdf.py       # PDF processing utility
│   ├── example_data.json    # Configuration template (committed)
│   ├── data.json           # Local configuration (user-created, not committed)
│   └── errorCodesTechnologies.db  # Generated database
├── media/                  # Images and resources
├── .github/                # Contribution and project standards
├── build/                  # Build artifacts
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Key Files & Development Guidelines

-   **`src/main.py`**: The main application entry point. 
    -   *Guideline*: Keep the GUI logic clean and responsive, separating it from business logic where possible.

-   **`src/process_pdf.py`**: A command-line utility for extracting error code tables from PDF manuals.
    -   *Guideline*: Ensure parsing logic is robust. Add specific modes (like `--sew-mode`) for vendor-specific PDF layouts.

-   **`src/data.json` / `src/example_data.json`**: Configuration files.
    -   *Guideline*: When adding features, always update `example_data.json` with generic, non-sensitive placeholders. Never commit `data.json`.

-   **`src/errorCodesTechnologies.db`**: The SQLite database.
    -   *Guideline*: If the schema changes, ensure migration paths are considered.

## Quick Test Guide

1.  **Run the application**: `python src/main.py`
2.  **Navigate the UI**: Select a technology and choose a task.
3.  **Test PDF Processing**: `python src/process_pdf.py --pdf-path "path/to/manual.pdf" ...`
