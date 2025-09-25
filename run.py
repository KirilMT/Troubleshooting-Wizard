import tkinter as tk
import json
import os
import logging
from src.main import MainApplication
from src.logging_config import setup_logging

def main():
    """Initializes and runs the Troubleshooting Wizard application."""
    setup_logging() # Initialize logging
    root = tk.Tk()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Prioritize loading data.json, fall back to example_data.json
    data_path = os.path.join(script_dir, "src", "data.json")
    example_data_path = os.path.join(script_dir, "src", "example_data.json")

    json_path_to_load = None
    if os.path.exists(data_path):
        json_path_to_load = data_path
        logging.info(f"Loading user configuration from {data_path}")
    elif os.path.exists(example_data_path):
        json_path_to_load = example_data_path
        logging.warning(f"User configuration 'data.json' not found. Falling back to {example_data_path}")

    if not json_path_to_load:
        error_msg = "Critical Error: Neither 'data.json' nor 'example_data.json' could be found in the 'src' directory."
        logging.critical(error_msg)
        # A GUI error would be better, but print is a robust fallback if tkinter fails.
        print(error_msg)
        return

    try:
        with open(json_path_to_load, 'r', encoding='utf-8') as f:
            initial_json_data = json.load(f)
    except json.JSONDecodeError:
        error_msg = f"Error: The data file at {json_path_to_load} is not a valid JSON file."
        logging.error(error_msg)
        print(error_msg)
        return

    app = MainApplication(root, initial_json_data, os.path.join(script_dir, "src"))
    root.mainloop()

if __name__ == "__main__":
    main()
