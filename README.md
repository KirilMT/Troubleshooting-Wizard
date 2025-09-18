# Industrial Troubleshooting Application

A Python-based GUI application for industrial equipment troubleshooting and error code management. This tool provides a centralized interface for accessing error codes, manuals, and troubleshooting resources for various manufacturing technologies.

## Features

- **Multi-Technology Support**: Configurable support for different industrial technologies (WTC, Lenze, FANUC, etc.)
- **Error Code Search**: Interactive search functionality for error codes with PDF integration
- **PDF Processing**: Extract and store error code tables from PDF manuals into SQLite database
- **Intuitive GUI**: User-friendly tkinter interface with navigation and search capabilities
- **Configuration-Driven**: JSON-based configuration for easy customization and maintenance

## Technologies Supported

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

## Installation

### Prerequisites

- Python 3.7 or higher
- Required Python packages (see requirements.txt)

### Setup

1. Clone or download this repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure your application**:
   - Copy `src/example_data.json` to `src/data.json`
   - Update `src/data.json` with your specific file paths and URLs
   - Replace example URLs with your actual document locations
4. **Setup media files**:
   - Replace placeholder files in `media/` with your actual error code screenshots
   - Add additional images as needed for your equipment
   - See `media/README.md` for detailed instructions
5. Run the application:
   ```bash
   python src/main.py
   ```

## Configuration

### Standard Configuration Approach

The application uses a dual-file configuration system designed for security and ease of use:

#### Configuration Files:
1. **`src/example_data.json`** (committed to repository)
   - Template with example URLs and standardized structure
   - Safe to commit to version control
   - Used as fallback if `data.json` doesn't exist
   - Contains generic `https://example.com/` URLs

2. **`src/data.json`** (user-created, not committed)
   - Copy from `example_data.json` and customize for your environment
   - Contains actual URLs, file paths, and credentials
   - Automatically ignored by git for security

#### Media Files:
1. **Example files** (committed)
   - `media/example_*.png` - Placeholder files showing structure
   - Safe generic examples for demonstration

2. **Your actual files** (not committed)
   - Replace examples with real screenshots and diagrams
   - Add new files as needed for your specific equipment
   - Automatically ignored by git to protect corporate data

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

1. Add a new technology section in your `data.json`
2. Define URL variables for your documents
3. Create tasks with appropriate task types:
   - `error_codes`: Interactive error code search with PDF automation
   - `open_url`: Direct URL/file opening
4. Add corresponding image files to the `media/` directory

### Path Configuration

- **Image paths**: Use relative paths like `../media/your_image.png`
- **Document URLs**: Use full URLs or local file paths
- **Variable substitution**: Use `{{variable_name}}` syntax for URL variables

## Usage

### Main Application

1. Launch the application: `python src/main.py`
2. Select a technology from the main menu
3. Choose from available tasks:
   - **Error Codes**: Search for specific error codes in manuals
   - **Manuals**: Open relevant documentation
   - **Flowcharts**: Access troubleshooting flowcharts

### PDF Processing Tool

Process PDF manuals to extract error code tables:

```bash
python src/process_pdf.py --pdf-path "path/to/manual.pdf" --table-name "error_codes" --start-page 1 --end-page 10
```

**Parameters:**
- `--pdf-path`: Full path to the PDF file
- `--table-name`: Database table name for storing extracted data
- `--start-page`: First page to process (1-based)
- `--end-page`: Last page to process (1-based)

## SEW Error Code Extraction

This application now supports robust extraction and storage of SEW Drive System error codes from PDF manuals.

### How to Extract SEW Error Codes

Run the PDF extraction utility with the `--sew-mode` option:

```bash
python src/process_pdf.py --pdf-path <path_to_sew_pdf> --start-page <first_page> --end-page <last_page> --sew-mode
```

This will extract SEW error codes (fault code, suberror code, description) and store them in the `sew_error_codes` table in `src/errorCodesTechnologies.db`.

### SEW Error Code Table Schema

- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `fault_code` (TEXT)
- `suberror_code` (TEXT)
- `description` (TEXT)

## Project Structure

```
├── src/
│   ├── main.py              # Main GUI application
│   ├── process_pdf.py       # PDF processing utility
│   ├── example_data.json    # Configuration template (committed)
│   ├── data.json           # Local configuration (user-created, not committed)
│   └── errorCodesTechnologies.db  # Generated database
├── media/                  # Images and resources
│   ├── README.md           # Media folder instructions
│   ├── example_*.png       # Example placeholder images (committed)
│   └── [your_files]        # Your actual images (not committed)
├── build/                  # Build artifacts
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Development

### Configuration Best Practices

1. **Never commit `src/data.json`** - Contains sensitive URLs and credentials
2. **Never commit corporate media files** - Only example placeholders are committed
3. **Update `src/example_data.json`** when adding new technologies or features
4. **Use relative paths** for media files in configuration
5. **Use example URLs** in `example_data.json` (like `https://example.com/path/to/file.pdf`)

### Security Features

- **Automatic data protection**: Real configuration and media files are automatically ignored by git
- **Template system**: Safe examples provided for structure reference
- **Sensitive data isolation**: All corporate-specific content stays local

### Code Style

This project follows PEP 8 Python style guidelines and uses object-oriented programming patterns.

### AI Assistant Instructions

Project-specific instructions for GitHub Copilot and other AI assistants are located in `.github/copilot-instructions.md`.

### Contributing

1. Ensure all new code includes proper error handling
2. Add docstrings for new classes and methods
3. Update `example_data.json` when adding new features
4. Test thoroughly across different environments
5. Keep configuration examples generic and non-sensitive

## Dependencies

See `requirements.txt` for the complete list of required packages.

## License

MIT License - Open source project for industrial troubleshooting applications.

## Support

For issues or questions, please open an issue in the project repository.
