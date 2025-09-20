import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import json
import webbrowser
import time
import pyautogui
import os
import sqlite3


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
        conn = None  # Ensure conn is initialized
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
        is_sew_technology = tech_data.get("button_text", "").lower().find("sew") != -1

        # --- NEW LOGIC: Pre-calculate required size for SEW view ---
        if is_sew_technology:
            # Create a hidden frame to measure required size
            temp_frame = ttk.Frame(self.root)
            temp_frame.pack_forget()
            self._show_sew_database_interface(temp_frame, measure_only=True)
            temp_frame.update_idletasks()
            req_width = temp_frame.winfo_reqwidth()
            req_height = temp_frame.winfo_reqheight()
            temp_frame.destroy()
            # Center window with measured size
            self._set_window_dimensions(req_width, req_height)
            error_codes_width = req_width
            error_codes_height = req_height

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

        if is_sew_technology:
            self._show_sew_database_interface(error_codes_frame)
        else:
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

    def _show_sew_database_interface(self, parent_frame, measure_only=False):
        """Show the SEW database search interface. If measure_only=True, just pack widgets for size calculation."""
        main_container = ttk.Frame(parent_frame)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        parent_frame.update_idletasks()

        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill="x", pady=(0, 10))
        title_frame.columnconfigure(0, weight=1)
        title_label = ttk.Label(
            title_frame,
            text="SEW MoviPro Error Code Database",
            font=("Segoe UI", 18, "bold"),
            foreground="#2E86AB",
            anchor="center",
            justify="center"
        )
        title_label.grid(row=0, column=0, sticky="ew")
        help_btn = ttk.Button(
            title_frame,
            text="?",
            width=2,
            command=self._show_help_image,
            style="Help.TButton"
        )
        help_btn.grid(row=0, column=1, sticky="e", padx=(10, 0))
        style = ttk.Style()
        style.configure("Help.TButton", font=("Segoe UI", 12, "bold"), foreground="#2E86AB")

        subtitle_label = ttk.Label(
            main_container,
            text="Search and troubleshoot SEW drive system error codes",
            font=("Segoe UI", 10),
            foreground="#666666",
            anchor="center",
            justify="center"
        )
        subtitle_label.pack(fill="x", pady=(0, 10))

        search_container = ttk.LabelFrame(main_container, text="Search Criteria", padding=15)
        search_container.pack(fill="x", pady=(0, 10))
        search_container.columnconfigure(1, weight=1)
        search_container.columnconfigure(3, weight=1)

        ttk.Label(search_container, text="Error Code:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 10))
        self.sew_error_code_entry = ttk.Entry(search_container, width=15, font=("Segoe UI", 10))
        self.sew_error_code_entry.grid(row=0, column=1, sticky="ew", pady=8, padx=(0, 20))
        ttk.Label(search_container, text="Suberror Code:", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", pady=8, padx=(0, 10))
        self.sew_suberror_code_entry = ttk.Entry(search_container, width=15, font=("Segoe UI", 10))
        self.sew_suberror_code_entry.grid(row=0, column=3, sticky="ew", pady=8)
        ttk.Label(search_container, text="Error Description:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=(16, 8), padx=(0, 10))
        self.sew_error_designation_entry = ttk.Entry(search_container, font=("Segoe UI", 10))
        self.sew_error_designation_entry.grid(row=1, column=1, columnspan=3, sticky="ew", pady=(16, 8))
        button_frame = ttk.Frame(search_container)
        button_frame.grid(row=2, column=0, columnspan=4, pady=(20, 0))
        search_button = ttk.Button(
            button_frame,
            text="🔍 Search Error Code",
            command=self.search_sew_error_codes,
            style="Accent.TButton"
        )
        search_button.pack()
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"))
        self.sew_error_code_entry.bind("<Return>", lambda e: self.search_sew_error_codes())
        self.sew_suberror_code_entry.bind("<Return>", lambda e: self.search_sew_error_codes())
        self.sew_error_designation_entry.bind("<Return>", lambda e: self.search_sew_error_codes())

        results_container = ttk.LabelFrame(main_container, text="Error Code Details", padding=15)
        results_container.pack(fill="both", expand=True, pady=(0, 10))
        self.results_frame = ttk.Frame(results_container)
        self.results_frame.pack(fill="both", expand=True)
        self._show_search_instructions()

        if not measure_only:
            self.root.update_idletasks()
            self.root.geometry("")

    def _show_help_image(self):
        """Show the help image in a modal popup window."""
        image_path = os.path.join(self.script_dir, "..", "media", "SEW_MoviPro_movitools_parameters.jpg")
        if not os.path.exists(image_path):
            image_path = os.path.join(self.script_dir, "media", "SEW_MoviPro_movitools_parameters.jpg")
        try:
            help_win = tk.Toplevel(self.root)
            help_win.title("SEW MoviPro Help")
            help_win.transient(self.root)
            help_win.grab_set()
            help_win.geometry("700x400")
            help_win.resizable(False, False)
            img = Image.open(image_path)
            img = img.resize((680, 320), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(help_win, image=photo)
            img_label.image = photo
            img_label.pack(padx=10, pady=10)
            close_btn = ttk.Button(help_win, text="Close", command=help_win.destroy)
            close_btn.pack(pady=(0, 10))
        except Exception as e:
            messagebox.showerror("Help Image Error", f"Could not load help image: {e}")

        # Center the help image popup on the screen (should be outside the except block)
        help_win.update_idletasks()
        popup_width = help_win.winfo_width()
        popup_height = help_win.winfo_height()
        screen_width = help_win.winfo_screenwidth()
        screen_height = help_win.winfo_screenheight()
        x = int((screen_width - popup_width) / 2)
        y = int((screen_height - popup_height) / 2)
        help_win.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

    def _show_search_instructions(self):
        """Show initial search instructions."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        instructions_frame = ttk.Frame(self.results_frame)
        instructions_frame.pack(fill="x", padx=20, pady=20)
        icon_label = ttk.Label(
            instructions_frame,
            text="🔍",
            font=("Segoe UI", 24)
        )
        icon_label.pack(pady=(0, 10))
        title_label = ttk.Label(
            instructions_frame,
            text="Search for SEW Error Codes",
            font=("Segoe UI", 14, "bold"),
            foreground="#2E86AB"
        )
        title_label.pack(pady=(0, 15))
        instructions_text = """Enter search criteria above and click 'Search Error Code':\n\n• Error Code: Main fault code (e.g., '01', '02', '03')\n• Suberror Code: Additional specification (e.g., '0', '1', '5')\n• Error Description: Partial description (e.g., 'Overcurrent')\n\nUse partial matches for better results."""
        instructions_label = ttk.Label(
            instructions_frame,
            text=instructions_text,
            font=("Segoe UI", 10),
            foreground="#666666",
            justify="left"
        )
        instructions_label.pack()

    def _format_single_line_content(self, text):
        """Format text content for single-line display (remove artificial newlines)."""
        if not text or text.strip() == "":
            return "Not specified"
        # Replace literal \n and actual newlines with a space, then collapse multiple spaces
        return ' '.join(text.replace("\\n", " ").replace("\n", " ").split())

    def _show_error_card(self, error_data):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        card_frame = ttk.Frame(self.results_frame)
        card_frame.pack(fill="x", padx=10, pady=10)
        header_frame = ttk.Frame(card_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        error_code_frame = ttk.Frame(header_frame)
        error_code_frame.pack(anchor="w")
        code_text = f"Error Code: {error_data.get('error_code', 'N/A')}"
        if error_data.get('suberror_code'):
            code_text += f".{error_data.get('suberror_code')}"
        ttk.Label(
            error_code_frame,
            text=code_text,
            font=("Segoe UI", 14, "bold"),
            foreground="#FFFFFF",
            background="#E74C3C",
            padding=(10, 5)
        ).pack(side="left")
        designation_label = ttk.Label(
            header_frame,
            text=self._format_single_line_content(error_data.get('error_designation', 'Unknown Error')),
            font=("Segoe UI", 16, "bold"),
            foreground="#2C3E50"
        )
        designation_label.pack(anchor="w", pady=(10, 0))
        if error_data.get('error_response'):
            response_label = ttk.Label(
                header_frame,
                text=f"Response: {self._format_single_line_content(error_data.get('error_response'))}",
                font=("Segoe UI", 11),
                foreground="#E67E22"
            )
            response_label.pack(anchor="w", pady=(5, 0))
        separator = ttk.Separator(card_frame, orient="horizontal")
        separator.pack(fill="x", pady=10)
        content_frame = ttk.Frame(card_frame)
        content_frame.pack(fill="x")
        if error_data.get('possible_cause'):
            causes_frame = ttk.LabelFrame(content_frame, text="🔍 Possible Causes", padding=10)
            causes_frame.pack(fill="x", pady=(0, 10))
            causes_text = tk.Label(
                causes_frame,
                text=self._format_text_content(error_data.get('possible_cause', '')),
                font=("Segoe UI", 10),
                background="#FFF5F5",
                foreground="#2C3E50",
                anchor="w",
                justify="left"
            )
            causes_text.pack(fill="x")
        if error_data.get('measure'):
            actions_frame = ttk.LabelFrame(content_frame, text="✅ Recommended Actions", padding=10)
            actions_frame.pack(fill="x")
            actions_text = tk.Label(
                actions_frame,
                text=self._format_text_content(error_data.get('measure', '')),
                font=("Segoe UI", 10),
                background="#F0FFF4",
                foreground="#2C3E50",
                anchor="w",
                justify="left"
            )
            actions_text.pack(fill="x")

    def _format_text_content(self, text):
        """Format text content for better readability while preserving structure and joining broken sentences."""
        if not text or text.strip() == "":
            return "Not specified"

        # Replace literal \n with actual newlines
        text = text.replace("\\n", "\n")

        # Split into lines and process them
        lines = text.split("\n")
        processed_lines = []
        current_line = ""

        for line in lines:
            line = line.strip()
            if not line:  # Skip empty lines
                continue

            # If this line starts with a bullet point, finish the current line and start a new one
            if line.startswith("•"):
                if current_line:
                    processed_lines.append(current_line.strip())
                current_line = line
            else:
                # This line doesn't start with a bullet point
                if current_line:
                    # If we have a current line, check if this should be joined to it
                    # Join if the current line doesn't end with punctuation that indicates end of sentence
                    if current_line.rstrip().endswith(('.', ':', '!', '?')):
                        # Current line ends with punctuation, start a new line
                        processed_lines.append(current_line.strip())
                        current_line = line
                    else:
                        # Join to current line with a space
                        current_line += " " + line
                else:
                    # No current line, start with this line
                    current_line = line

        # Don't forget the last line
        if current_line:
            processed_lines.append(current_line.strip())

        return "\n".join(processed_lines) if processed_lines else "Not specified"

    def _show_no_results(self):
        """Show no results found message."""
        # Clear any existing content
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        no_results_frame = ttk.Frame(self.results_frame)
        no_results_frame.pack(fill="x", padx=20, pady=40)

        # Icon
        icon_label = ttk.Label(
            no_results_frame,
            text="❌",
            font=("Segoe UI", 24)
        )
        icon_label.pack(pady=(0, 10))

        # Message
        title_label = ttk.Label(
            no_results_frame,
            text="No Error Code Found",
            font=("Segoe UI", 14, "bold"),
            foreground="#E74C3C"
        )
        title_label.pack(pady=(0, 15))

        suggestions_text = """Try these suggestions:

• Use partial matches (e.g., "01" instead of "01.0")
• Check spelling of error descriptions
• Try searching with just the main error code
• Verify the error code exists in the database"""

        suggestions_label = ttk.Label(
            no_results_frame,
            text=suggestions_text,
            font=("Segoe UI", 10),
            foreground="#666666",
            justify="left"
        )
        suggestions_label.pack()

    def search_sew_error_codes(self):
        """Search for SEW error codes and display the first matching result."""
        # Remove the image if present
        if hasattr(self, 'sew_image_label') and self.sew_image_label:
            self.sew_image_label.destroy()
            self.sew_image_label = None

        error_code = self.sew_error_code_entry.get().strip()
        suberror_code = self.sew_suberror_code_entry.get().strip()
        error_designation = self.sew_error_designation_entry.get().strip()

        if not any([error_code, suberror_code, error_designation]):
            self._show_search_instructions()
            # --- Measure the full SEW error code view and resize/center window to its default size ---
            temp_frame = ttk.Frame(self.root)
            temp_frame.pack_forget()
            self._show_sew_database_interface(temp_frame, measure_only=True)
            temp_frame.update_idletasks()
            req_width = temp_frame.winfo_reqwidth()
            req_height = temp_frame.winfo_reqheight()
            temp_frame.destroy()
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - req_width) // 2
            y = (screen_height - req_height) // 2
            self.root.geometry(f"{req_width}x{req_height}+{x}+{y}")
            return

        # Construct the correct database path
        db_path = os.path.join(self.script_dir, "errorCodesTechnologies.db")

        # Initialize the database manager
        db_manager = SEWDatabaseManager(db_path)

        # Search for error codes
        results = db_manager.search_error_codes(error_code, suberror_code, error_designation)

        if results:
            # Show only the first matching result
            self._show_error_card(results[0])
        else:
            self._show_no_results()

        # --- Center window after resizing for results or no results ---
        self.root.update_idletasks()
        new_width = self.root.winfo_width()
        new_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - new_width) // 2
        y = (screen_height - new_height) // 2
        self.root.geometry(f"{new_width}x{new_height}+{x}+{y}")

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
