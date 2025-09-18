import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json
import webbrowser
import time
import pyautogui
import os
import sqlite3
from tkinter import scrolledtext


class SEWDatabaseManager:
    """Manages SEW error code database operations."""

    def __init__(self, db_path):
        self.db_path = db_path

    def search_error_codes(self, error_code=None, suberror_code=None, error_designation=None):
        """
        Search for SEW error codes based on provided criteria.

        Args:
            error_code (str): Main error code to search for
            suberror_code (str): Suberror code to search for
            error_designation (str): Error designation to search for

        Returns:
            list: List of matching error code records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build dynamic query based on provided criteria
            conditions = []
            params = []

            if error_code and error_code.strip():
                conditions.append("error_code LIKE ?")
                params.append(f"%{error_code.strip()}%")

            if suberror_code and suberror_code.strip():
                conditions.append("suberror_code LIKE ?")
                params.append(f"%{suberror_code.strip()}%")

            if error_designation and error_designation.strip():
                conditions.append("error_designation LIKE ?")
                params.append(f"%{error_designation.strip()}%")

            if not conditions:
                # If no search criteria provided, return empty list
                return []

            query = "SELECT * FROM sew_error_codes_detailed WHERE " + " AND ".join(conditions)
            cursor.execute(query, params)
            results = cursor.fetchall()

            # Convert to list of dictionaries for easier handling
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in results]

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if conn:
                conn.close()


class MainApplication:
    def __init__(self, root_window, initial_json_data, script_dir):
        self.root = root_window
        self.root.title(initial_json_data["MainApplication"]["title"])
        self.script_dir = script_dir

        # Get the window dimensions from JSON data
        self.initial_width = initial_json_data["MainApplication"]["width"]
        self.initial_height = initial_json_data["MainApplication"]["height"]
        self._set_window_dimensions(self.initial_width, self.initial_height)  # Center the window

        self.json_data = initial_json_data
        self.current_view = None
        self.view_stack = []  # Stack to manage view history

        self.variables = {}  # Initialize variables dictionary

        self.show_main_program()  # Show the Main Program initially

    def _set_window_dimensions(self, width, height):
        """Set window dimensions and center it on screen."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _search_pdf(self, fault_message, url_path):
        """Open PDF and search for fault message using browser automation."""
        # Open the PDF file in a web browser
        webbrowser.open(url_path)

        # Wait for the specified wait time for the PDF file to load
        time.sleep(2)

        # Simulate pressing Ctrl + F
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(1)

        # Type the search string and press Enter
        pyautogui.typewrite(fault_message)
        pyautogui.press('enter')

    def show_main_program(self):
        self.destroy_current_view()
        self.view_stack.clear()  # Clear the view history
        self._set_window_dimensions(self.initial_width, self.initial_height)

        main_program_frame = ttk.Frame(self.root)
        main_program_frame.pack(fill="both", expand=True)
        self.current_view = main_program_frame

        technologies_data = self.json_data["MainApplication"]["Technologies"]
        for tech_name, tech_data in technologies_data.items():
            tech_button = ttk.Button(
                main_program_frame,
                text=tech_data.get("button_text", ""),
                command=lambda data=tech_data: self.show_technology(data)
            )
            tech_button.pack(padx=10, pady=10)  # Place the Technologies button vertically

    def show_technology(self, tech_data):
        self.destroy_current_view()
        self.view_stack.append((self.show_main_program, None))

        tech_width = tech_data.get("width", self.initial_width)
        tech_height = tech_data.get("height", self.initial_height)

        tech_frame = ttk.Frame(self.root)
        tech_frame.pack(fill="both", expand=True)
        self.current_view = tech_frame

        if tech_width and tech_height:
            # Set dimensions only if they are provided in the JSON data
            self._set_window_dimensions(tech_width, tech_height)

        # Extract variables data for the current technology from the JSON configuration
        self.variables = tech_data

        back_button = ttk.Button(
            tech_frame,
            text="< Back to Technologies",
            command=self.show_previous_view  # Use the previous view function
        )
        back_button.pack(side="left", anchor="nw", padx=10, pady=10)  # Move to the top-left corner

        self._modify_tasks(tech_data)  # Modify and create task buttons

    def _modify_tasks(self, tech_data):
        """Create task buttons for the current technology."""
        tasks = tech_data.get("tasks", [])
        for index, task_data in enumerate(tasks):
            # Extract task attributes from the task_data dictionary
            task_title = list(task_data.keys())[0]
            task_attributes = task_data[task_title]

            # Replace variables in the URL paths with their values
            task_attributes["url_path"] = self._replace_variables(task_attributes.get("url_path", ""))

            # Define custom style for the first button with a yellow background
            style = ttk.Style()
            style.configure("Yellow.TButton", background="yellow")

            button = ttk.Button(
                self.current_view,  # Use the current view frame
                text=task_title,
                command=lambda attrs=task_attributes, tech=tech_data: self.show_task(attrs, tech),
                style="Yellow.TButton" if index == 0 else None  # Apply custom style to the first button
            )
            button.pack(pady=10)

    def show_task(self, task_attributes, tech_data):
        task_type = task_attributes.get("task_type")

        if task_type == "error_codes":
            self.show_error_codes(task_attributes, tech_data)
        elif task_type == "open_url":
            self._open_url(task_attributes.get("url_path"), task_attributes.get("pdf_page_number"))

    def _open_url(self, url_path, pdf_page_number=None):
        """Open URL or PDF with optional page number."""
        # If a page number is provided, construct the URL with the page number
        if pdf_page_number is not None:
            url_with_page = self._replace_variables(f"{url_path}#page={pdf_page_number}")
            webbrowser.open(url_with_page)
        else:
            # Open the PDF with the default web browser
            url_path = self._replace_variables(url_path)
            webbrowser.open(url_path)

    def show_error_codes(self, task_attributes, tech_data):
        self.destroy_current_view()
        self.view_stack.append((self.show_technology, tech_data))

        error_codes_width = task_attributes.get("width", 800)
        error_codes_height = task_attributes.get("height", 730)
        image_path = task_attributes.get("image_path", "")

        # Check if this is SEW technology for database functionality
        is_sew_technology = tech_data.get("button_text", "").lower().find("sew") != -1

        error_codes_frame = ttk.Frame(self.root)
        error_codes_frame.pack(fill="both", expand=True)
        self.current_view = error_codes_frame

        # Center the error_codes window
        self._set_window_dimensions(error_codes_width, error_codes_height)

        button_frame = ttk.Frame(error_codes_frame)
        button_frame.pack(side="top", anchor="nw", padx=10, pady=10)

        home_button = ttk.Button(
            button_frame,
            text="< Back to Technologies",
            command=self.show_main_program
        )
        home_button.pack(side="left", padx=10)

        back_button = ttk.Button(
            button_frame,
            text="< Back to Tasks",
            command=self.show_previous_view
        )
        back_button.pack(side="left", padx=10)

        try:
            if image_path:
                abs_image_path = os.path.abspath(os.path.join(self.script_dir, image_path))
                image = Image.open(abs_image_path)
                photo = ImageTk.PhotoImage(image)
                image_label = ttk.Label(error_codes_frame, image=photo)
                image_label.image = photo
                image_label.pack(pady=10)
        except Exception as e:
            print(f"Error loading image: {e}")

        # Show SEW database search interface if this is SEW technology
        if is_sew_technology:
            self._show_sew_database_interface(error_codes_frame)
        else:
            # Show traditional PDF search interface for other technologies
            self._show_traditional_search_interface(error_codes_frame, task_attributes)

    def _show_traditional_search_interface(self, parent_frame, task_attributes):
        """Show the traditional PDF search interface for non-SEW technologies."""
        label_frame = ttk.Frame(parent_frame)
        label_frame.pack(pady=10)

        label_style = ttk.Style()
        label_style.configure("Bold.TLabel", font=("Helvetica", 15, "bold"))
        ttk.Label(label_frame, text="Insert fault code/message:", style="Bold.TLabel").pack(side="left")

        entry_style = ttk.Style()
        entry_style.configure("Large.TEntry", font=("Helvetica", 16))

        search_entry = ttk.Entry(label_frame, style="Large.TEntry", width=65)
        search_entry.pack(side="left", padx=10)

        search_button = ttk.Button(
            parent_frame,
            text="Search",
            command=lambda: self._search_pdf(search_entry.get(), task_attributes.get("url_path"))
        )
        search_button.pack(side="right", padx=10)

    def _show_sew_database_interface(self, parent_frame):
        """Show the SEW database search interface."""
        # Title
        sew_title = ttk.Label(parent_frame, text="SEW Error Code Database Search",
                             font=("Helvetica", 16, "bold"))
        sew_title.pack(pady=10)

        # Search form
        search_frame = ttk.LabelFrame(parent_frame, text="Search Criteria", padding=10)
        search_frame.pack(pady=10, padx=20, fill="x")

        # Error Code field
        ttk.Label(search_frame, text="Error Code:").grid(row=0, column=0, sticky="w", pady=5)
        self.sew_error_code_entry = ttk.Entry(search_frame, width=30)
        self.sew_error_code_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # Suberror Code field
        ttk.Label(search_frame, text="Suberror Code:").grid(row=1, column=0, sticky="w", pady=5)
        self.sew_suberror_code_entry = ttk.Entry(search_frame, width=30)
        self.sew_suberror_code_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Error Designation field
        ttk.Label(search_frame, text="Error Designation:").grid(row=2, column=0, sticky="w", pady=5)
        self.sew_error_designation_entry = ttk.Entry(search_frame, width=30)
        self.sew_error_designation_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Configure column weight for resizing
        search_frame.columnconfigure(1, weight=1)

        # Search button
        search_button = ttk.Button(
            search_frame,
            text="Search SEW Error Codes",
            command=self.search_sew_error_codes
        )
        search_button.grid(row=3, column=0, columnspan=2, pady=15)

        # Results area
        results_frame = ttk.LabelFrame(parent_frame, text="Search Results", padding=10)
        results_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.sew_results_text = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            height=15,
            font=("Consolas", 10)
        )
        self.sew_results_text.pack(fill="both", expand=True)

        # Instructions
        instructions = """Instructions:
• Enter at least one search criterion (Error Code, Suberror Code, or Error Designation)
• You can use partial matches - e.g., enter "01" to find all error codes containing "01"
• Leave fields empty to ignore them in the search
• Error Code: Main fault code (e.g., "01", "02", "03")
• Suberror Code: Additional error specification (e.g., "0", "1", "5")
• Error Designation: Error name/description (e.g., "Overcurrent", "Overvoltage")"""

        self.sew_results_text.insert(tk.END, instructions)

    def search_sew_error_codes(self):
        """Search for SEW error codes and display results in the text box."""
        error_code = self.sew_error_code_entry.get()
        suberror_code = self.sew_suberror_code_entry.get()
        error_designation = self.sew_error_designation_entry.get()

        # Construct the correct database path
        db_path = os.path.join(self.script_dir, "errorCodesTechnologies.db")

        # Initialize the database manager
        db_manager = SEWDatabaseManager(db_path)

        # Search for error codes
        results = db_manager.search_error_codes(error_code, suberror_code, error_designation)

        # Clear previous results
        self.sew_results_text.delete(1.0, tk.END)

        if results:
            self.sew_results_text.insert(tk.END, f"Found {len(results)} matching error code(s):\n")
            self.sew_results_text.insert(tk.END, "=" * 80 + "\n\n")

            for i, result in enumerate(results, 1):
                self.sew_results_text.insert(tk.END, f"RESULT {i}:\n")
                self.sew_results_text.insert(tk.END, f"Error Code: {result['error_code']}\n")
                self.sew_results_text.insert(tk.END, f"Error Designation: {result['error_designation']}\n")
                self.sew_results_text.insert(tk.END, f"Error Response: {result['error_response']}\n")
                self.sew_results_text.insert(tk.END, f"Suberror Code: {result['suberror_code']}\n")
                self.sew_results_text.insert(tk.END, f"Suberror Designation: {result['suberror_designation']}\n")
                self.sew_results_text.insert(tk.END, f"\nPossible Cause:\n{result['possible_cause']}\n")
                self.sew_results_text.insert(tk.END, f"\nRecommended Measure:\n{result['measure']}\n")
                self.sew_results_text.insert(tk.END, "\n" + "=" * 80 + "\n\n")
        else:
            self.sew_results_text.insert(tk.END, "No matching error codes found.\n\n")
            self.sew_results_text.insert(tk.END, "Please check your search criteria:\n")
            self.sew_results_text.insert(tk.END, "• Make sure at least one field is filled\n")
            self.sew_results_text.insert(tk.END, "• Try using partial matches (e.g., '01' instead of '01.0')\n")
            self.sew_results_text.insert(tk.END, "• Check spelling of error designations\n")

    def _replace_variables(self, text):
        """Replace variables in double curly braces with their values from the JSON configuration."""
        while "{{" in text and "}}" in text:
            start_index = text.find("{{")
            end_index = text.find("}}")
            if start_index < end_index:
                variable_name = text[start_index + 2:end_index]
                if variable_name in self.variables:
                    replacement = self.variables[variable_name]
                    text = text[:start_index] + replacement + text[end_index + 2:]
                else:
                    break
            else:
                break
        return text

    def destroy_current_view(self):
        if self.current_view:
            self.current_view.destroy()

    def show_previous_view(self):
        if self.view_stack:
            self.destroy_current_view()
            previous_view_func, previous_view_data = self.view_stack.pop()
            if previous_view_data:
                previous_view_func(previous_view_data)
            else:
                previous_view_func()


if __name__ == "__main__":
    root = tk.Tk()

    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Try to load the local data file, fall back to the example file
    data_file_path = os.path.join(script_dir, "data.json")
    if not os.path.exists(data_file_path):
        data_file_path = os.path.join(script_dir, "example_data.json")

    with open(data_file_path, "r") as json_file:
        json_data = json.load(json_file)

    app = MainApplication(root, json_data, script_dir)
    root.mainloop()
