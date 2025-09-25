# Troubleshooting-Wizard

A Python-based GUI application for industrial equipment troubleshooting and error code management. This tool provides a centralized interface for accessing error codes, manuals, and troubleshooting resources for various manufacturing technologies.

## 🚀 Features

- **Multi-Technology Support**: Configurable support for different industrial technologies.
- **Error Code Search**: Interactive search functionality for error codes with PDF integration.
- **PDF Processing**: Extract and store error code tables from PDF manuals into an SQLite database.
- **Intuitive GUI**: User-friendly tkinter interface with navigation and search capabilities.
- **Configuration-Driven**: JSON-based configuration for easy customization and maintenance.
- **Security**: Sensitive data (configuration, media files) is kept local and excluded from version control by default.

## 🖼️ Screenshots

*(Please add screenshots of your application to the `media/` directory and update the links below.)*

| Main Menu | Error Code Search |
| :---: | :---: |
| *Users can select a technology from the main menu.* | *Search for specific error codes within PDF manuals.* |
| ![Main Menu](media/example_main_menu.png) | ![Error Code Search](media/example_search.png) |

## 🛠️ Technologies Supported

- WTC (Welding Technology Corporation) Controllers
- Lenze Drive Systems
- FANUC Robotics Systems
- Atlas Copco Systems
- Clinching Systems
- Control Systems
- Tightening Systems
- Laser Systems
- SEW Drive Systems
- And more (easily extensible via configuration)

## 📁 Project Structure

```
Troubleshooting-Wizard/
├── logs/
│   └── app.log              # Application log files (auto-generated)
├── src/
│   ├── __init__.py          # Defines src as a Python package
│   ├── main.py              # Main GUI application logic
│   ├── process_pdf.py       # PDF processing utility
│   ├── logging_config.py    # Centralized logging configuration
│   ├── example_data.json    # Configuration template
│   └── errorCodesTechnologies.db  # Generated database
├── media/                  # Images and resources
│   ├── README.md           # Media folder instructions
│   ├── example_*.png       # Example placeholder images (committed)
│   └── [your_files]        # Your actual images (not committed)
├── .github/                # Contribution and project standards
├── build/                  # Build artifacts
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
├── run.py                 # Main entry point to run the application
└── README.md              # This file
```

## ⚙️ Setup and Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- Git

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2.  **Create and activate a virtual environment:**
    ```powershell
    # For Windows (PowerShell)
    py -3 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```
    ```bash
    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your application**:
    - Create `src/data.json` by copying the example file:
      ```bash
      cp src/example_data.json src/data.json
      ```
    - Update `src/data.json` with your specific file paths and URLs. This file is ignored by Git.

5.  **Set up media files**:
    - Place your actual error code screenshots, manuals, and diagrams in the `media/` directory.
    - See `media/README.md` for detailed instructions.

## ▶️ Running the Application

Once you have completed the setup and installation, you can run the application from the root directory of the project:

```bash
python run.py
```

## 📝 Logging

The application is configured with a robust logging system that captures informational messages, warnings, and errors.

- **Log Files**: Logs are automatically saved in the `logs/` directory.
- **Rotation**: A new log file is created daily, and logs are kept for up to 7 days.
- **Purpose**: These logs are invaluable for debugging issues and understanding the application's behavior over time.

## 🔧 Configuration

The application uses a dual-file configuration system for security and ease of use:

1.  **`src/example_data.json`** (Committed to repository)
    - A template with example URLs and a standardized structure. It's safe to commit.
2.  **`src/data.json`** (User-created, not committed)
    - Your local configuration containing actual URLs, file paths, and credentials. It is automatically ignored by Git.

### Configuration Structure
```json
{
  "MainApplication": {
    "title": "Your Application Title",
    "width": 350,
    "height": 470,
    "Technologies": {
      "TechnologyName": {
        "button_text": "Display Name",
        "url_variable_name": "https://your-actual-url.com/path/to/file.pdf",
        "tasks": ["..."]
      }
    }
  }
}
```

### Adding New Technologies
1.  Add a new technology section in your `data.json`.
2.  Define URL variables for your documents.
3.  Create tasks with appropriate types: `error_codes` or `open_url`.
4.  Add corresponding image files to the `media/` directory.

### Path Configuration
-   **Image paths**: Use relative paths like `../media/your_image.png`.
-   **Document URLs**: Use full URLs or local file paths.
-   **Variable substitution**: Use `{{variable_name}}` syntax for URL variables.

## 🎯 Usage

### Main Application
1.  Launch the application: `python run.py`
2.  Select a technology from the main menu.
3.  Choose from available tasks (e.g., search error codes, open manuals).

### PDF Processing Tool
Process PDF manuals to extract error code tables into the database:
```bash
python src/process_pdf.py --pdf-path "path/to/manual.pdf" --table-name "error_codes" --start-page 1 --end-page 10
```
**Parameters:**
- `--pdf-path`: Full path to the PDF file.
- `--table-name`: Database table name for storing data.
- `--start-page`: First page to process.
- `--end-page`: Last page to process.

### SEW Error Code Extraction
This application supports robust extraction of SEW Drive System error codes. Run the utility with the `--sew-mode` flag:
```bash
python src/process_pdf.py --pdf-path <path_to_sew_pdf> --start-page <first_page> --end-page <last_page> --sew-mode
```
This will store the results in the `sew_error_codes` table in `src/errorCodesTechnologies.db`.

## 🧑‍💻 Development

### Configuration Best Practices
1.  **Never commit `src/data.json`** or corporate media files.
2.  Update `src/example_data.json` when adding new features.
3.  Use relative paths for media files and placeholder URLs in `example_data.json`.

### Security Features
-   **Automatic data protection**: Real configuration and media files are automatically ignored by git.
-   **Sensitive data isolation**: All corporate-specific content stays local.

### Code Style
This project follows PEP 8 Python style guidelines and uses object-oriented programming patterns.

## 🤝 Contributing

We welcome contributions! Please see the `CONTRIBUTING.md` file for detailed guidelines on the development workflow, commit messages, and the review process. Project-specific instructions for AI assistants are located in `.github/copilot-instructions.md`.

## 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 💬 Support

For issues or questions, please open an issue in the project repository.

---
**Version: 1.0.1**
