# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-09-25

### Added
- **Robust Logging System**: Implemented a centralized, file-based logging system that saves daily logs to a `logs/` directory.
- **Root Entry Point**: Created a `run.py` file in the root directory to provide a clean, standard entry point for the application.
- **Enhanced Error Handling**: Added checks to gracefully handle missing database and configuration files, showing user-friendly error messages.
- **PDF Search Navigation**: Added "Next" and "Previous" buttons to the PDF viewer to easily navigate between search results, along with a `(current/total)` counter.

### Changed
- **Asynchronous PDF Search**: The PDF viewer now opens instantly and performs searches in the background, dramatically improving UI responsiveness.
- **Project Structure**: Refined the project structure by adding `run.py` and a `logging_config.py` module, and ensuring `src` is a proper package.
- **Code Quality & Refactoring**:
    - Centralized all UI styles into a single method for easier theme management.
    - Secured the PDF processing script against potential SQL injection by validating table names.
    - Standardized all Python scripts to follow PEP 8 conventions, such as placing all imports at the top of the file.

### Fixed
- **PDF Viewer Zoom Jump**: Fixed a critical bug where zooming would cause the view to jump to an incorrect page. The viewer now maintains its position during zoom operations.
- **PDF Viewer Zoom Out**: Corrected an issue that prevented zooming out to less than 100%.
- **PDF Viewer Spurious Scrolling**: Fixed a bug where clicking the zoom buttons would also incorrectly scroll the document.

## [1.0.1] - 2024-07-31

### Changed
- **Documentation Fix**: Performed a final meticulous review of all professional documentation (`README.md`, `.github/` files, etc.).
- **Improved `README.md`**: Ensured the `README.md` perfectly merges a professional structure with all critical project-specific details, including `Technologies Supported`, `Configuration`, and `Usage` sections.
- **Corrected Project Structure**: Verified that the project structure is accurately represented in all relevant documentation.

## [1.0.0] - 2024-07-31

### Added
- **Initial Project Setup**: First version of the Troubleshooting-Wizard.
- **Core Features**:
    - Multi-technology support for various industrial systems.
    - Interactive error code search with PDF processing.
    - User-friendly GUI built with tkinter.
- **Professional Documentation**: Created a full suite of professional repository documents:
    - A comprehensive `README.md` with setup, usage, and configuration details.
    - A `.github` directory containing `AGENT.md`, `copilot-instructions.md`, `GIT_WORKFLOW.md`, `CODEOWNERS`, and `CONTRIBUTING.md`.
    - A `CHANGELOG.md` to track versions.
    - An MIT `LICENSE` file.
