import tkinter as tk
from tkinter import messagebox
import json
import os
import logging
from src.main import MainApplication
from src.logging_config import setup_logging

def main():
    """Initializes and runs the Troubleshooting Wizard application."""
    setup_logging() # Initialize logging
    
    # Create the root window but hide it initially
    root = tk.Tk()
    root.withdraw()

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
        messagebox.showerror("Configuration Error", error_msg)
        root.destroy()
        return

    try:
        with open(json_path_to_load, 'r', encoding='utf-8') as f:
            initial_json_data = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Error: The data file at {json_path_to_load} is corrupted or not a valid JSON file.\n\nDetails: {e}"
        logging.error(error_msg)
        messagebox.showerror("JSON Error", error_msg)
        root.destroy()
        return
    except Exception as e:
        error_msg = f"An unexpected error occurred while loading {json_path_to_load}.\n\nDetails: {e}"
        logging.critical(error_msg)
        messagebox.showerror("File Load Error", error_msg)
        root.destroy()
        return

    # If everything is fine, show the window and run the app
    root.deiconify() 
    app = MainApplication(root, initial_json_data, os.path.join(script_dir, "src"))
    root.mainloop()

if __name__ == "__main__":
    main()
