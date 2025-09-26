"""
Refactored Main Application Module for Troubleshooting Wizard

This module contains the simplified MainApplication class that uses
the modular components from separate modules.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import json
import os
import logging
from typing import Dict, Any, List, Tuple, Optional

# Import from our new modules
from .pdf_viewer import PDFViewerWindow
from .database_manager import SEWDatabaseManager
from .ui_components import UIStyleManager


class MainApplication:
    def __init__(self, root_window: tk.Tk, initial_json_data: Dict[str, Any], script_dir: str) -> None:
        self.root = root_window
        self.root.title(initial_json_data["MainApplication"]["title"])
        self.script_dir = script_dir # This is now the project root
        self.initial_width = initial_json_data["MainApplication"]["width"]
        self.initial_height = initial_json_data["MainApplication"]["height"]
        self._set_window_dimensions(self.initial_width, self.initial_height)
        self.json_data = initial_json_data
        self.current_view = None
        self.view_stack = []
        self.variables = {}
        
        # Initialize UI style manager
        self.ui_style = UIStyleManager()
        
        self.show_main_program()

    def _set_window_dimensions(self, width: int, height: int) -> None:
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def show_main_program(self) -> None:
        self.destroy_current_view()
        self.view_stack.clear()
        # Set technology theme
        bg_color = self.ui_style.set_window_theme(self.root, 'technology')
        main_program_frame = self.ui_style.create_modern_frame(self.root, bg=bg_color)
        main_program_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.current_view = main_program_frame
        
        technologies_data = self.json_data["MainApplication"]["Technologies"]
        tech_list = list(technologies_data.items())
        
        # Create grid layout: max 10 rows per column
        for i, (tech_name, tech_data) in enumerate(tech_list):
            row = i % 10
            col = i // 10
            tech_button = self.ui_style.create_modern_button(
                main_program_frame, 
                tech_data.get("button_text", ""), 
                lambda data=tech_data: self.show_technology(data), 
                style='technology'
            )
            tech_button.grid(row=row, column=col, padx=5, pady=3, sticky="ew")
            main_program_frame.columnconfigure(col, weight=1)
        
        # Dynamic sizing
        self.root.update_idletasks()
        req_width = max(200, main_program_frame.winfo_reqwidth() + 20)
        req_height = main_program_frame.winfo_reqheight() + 20
        self._set_window_dimensions(req_width, req_height)

    def show_technology(self, tech_data: Dict[str, Any]) -> None:
        self.destroy_current_view()
        self.view_stack.append((self.show_main_program, None))
        # Set task theme
        bg_color = self.ui_style.set_window_theme(self.root, 'task')
        tech_frame = self.ui_style.create_modern_frame(self.root, bg=bg_color)
        tech_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.current_view = tech_frame
        self.variables = tech_data
        
        # Create standardized back button area
        self.ui_style.create_back_button_area(
            tech_frame, 
            self.json_data["labels"]["back_to_technologies"], 
            self.show_previous_view
        )
        
        self._modify_tasks(tech_data)
        
        # Dynamic sizing
        self.root.update_idletasks()
        req_width = max(200, tech_frame.winfo_reqwidth() + 20)
        req_height = tech_frame.winfo_reqheight() + 20
        self._set_window_dimensions(req_width, req_height)

    def _modify_tasks(self, tech_data: Dict[str, Any]) -> None:
        tasks = tech_data.get("tasks", [])
        for index, task_data in enumerate(tasks):
            task_title = list(task_data.keys())[0]
            task_attributes = task_data[task_title]
            task_attributes["url_path"] = self._replace_variables(task_attributes.get("url_path", ""))
            
            # Error codes button gets critical styling, others get task styling
            task_title_lower = task_title.lower()
            if 'error' in task_title_lower and ('code' in task_title_lower or 'codes' in task_title_lower):
                button_style = 'error_critical'
            else:
                button_style = 'task'
                
            button = self.ui_style.create_modern_button(
                self.current_view, 
                task_title, 
                lambda attrs=task_attributes, tech=tech_data: self.show_task(attrs, tech), 
                style=button_style
            )
            button.pack(pady=3)

    def show_task(self, task_attributes: Dict[str, Any], tech_data: Dict[str, Any]) -> None:
        task_type = task_attributes.get("task_type")
        if task_type == "error_codes":
            self.show_error_codes(task_attributes, tech_data)
        elif task_type == "open_url":
            url_path = task_attributes.get("url_path")
            # Get page identifier. If not present, it will be None.
            page_identifier = task_attributes.get("pdf_page_number") 
            if url_path:
                self._open_pdf_viewer(url_path, page_number=page_identifier)
            else:
                logging.error("Task with type 'open_url' is missing a 'url_path'.")
                messagebox.showwarning("Configuration Error", "This task is configured to open a file, but the file path is missing.")

    def show_error_codes(self, task_attributes: Dict[str, Any], tech_data: Dict[str, Any]) -> None:
        self.destroy_current_view()
        self.view_stack.append((self.show_technology, tech_data))
        
        is_sew_technology = tech_data.get("button_text", "").lower().find("sew") != -1

        # --- Robustness Check for SEW Database ---
        if is_sew_technology:
            db_path = os.path.join(self.script_dir, "data", "errorCodesTechnologies.db")
            if not os.path.exists(db_path):
                logging.critical(f"Database file not found at expected path: {db_path}")
                messagebox.showerror(
                    "Database Not Found",
                    f"The SEW error code database could not be found.\n\nExpected at: {db_path}"
                )
                # Revert to the previous view since we cannot proceed
                self.show_previous_view()
                return

        # Set error theme and create frame
        bg_color = self.ui_style.set_window_theme(self.root, 'error')
        error_codes_frame = self.ui_style.create_modern_frame(self.root, bg=bg_color)
        error_codes_frame.pack(fill="both", expand=True)
        self.current_view = error_codes_frame
        
        # Create dual navigation buttons
        self.ui_style.create_dual_back_button_area(
            error_codes_frame, 
            self.json_data["labels"]["back_to_technologies"], 
            self.show_main_program,
            self.json_data["labels"]["back_to_tasks"], 
            self.show_previous_view
        )
        
        if is_sew_technology:
            self._show_sew_database_interface(error_codes_frame)
        else:
            self._show_traditional_search_interface(error_codes_frame, task_attributes)
        
        # Dynamic sizing after content is created
        self.root.update_idletasks()
        screen_height = self.root.winfo_screenheight()
        max_height = int(screen_height * 0.85)
        if is_sew_technology:
            # Use compact dimensions for SEW interface (laptop-friendly)
            req_width = min(650, max(400, error_codes_frame.winfo_reqwidth() + 20))
            req_height = min(max_height, max(400, error_codes_frame.winfo_reqheight()))
        else:
            req_width = max(400, error_codes_frame.winfo_reqwidth() + 20)
            req_height = max(300, error_codes_frame.winfo_reqheight() + 20)
        self._set_window_dimensions(req_width, req_height)

    def _show_traditional_search_interface(self, parent_frame, task_attributes):
        # Main content area (minimal padding)
        content_frame = self.ui_style.create_modern_frame(parent_frame, bg=parent_frame['bg'])
        content_frame.pack(fill='both', expand=True, padx=5)
        
        # Display the configured image if available (center-aligned)
        image_path = task_attributes.get("image_path")
        if image_path:
            image_container = self.ui_style.create_modern_frame(content_frame, bg=parent_frame['bg'])
            image_container.pack()
            self._display_error_code_image(image_container, image_path)
        
        # Search input frame (center-aligned)
        input_frame = self.ui_style.create_modern_frame(content_frame, bg=parent_frame['bg'])
        input_frame.pack(pady=(8, 0))
        input_frame.grid_columnconfigure(1, weight=1)
        
        search_label = self.ui_style.create_modern_label(input_frame, 
                                                        self.json_data["labels"]["insert_fault_code"], 
                                                        style='title', bg=parent_frame['bg'])
        search_label.grid(row=0, column=0, sticky="w")
        
        search_entry = self.ui_style.create_modern_entry(input_frame, width=42)
        search_entry.grid(row=0, column=1, sticky="w", padx=(10, 0), ipady=5)
        
        # Search button on new row, aligned to right edge of entry
        search_button = self.ui_style.create_modern_button(input_frame, self.json_data["labels"]["search"], 
                                                          lambda: self._open_pdf_viewer(task_attributes.get("url_path"), search_term=search_entry.get()),
                                                          style='submit')
        search_button.grid(row=1, column=1, sticky="e", pady=(8, 0))
        
        # Bind Enter key to search
        search_entry.bind("<Return>", lambda e: self._open_pdf_viewer(task_attributes.get("url_path"), search_term=search_entry.get()))

    def _show_sew_database_interface(self, parent_frame, measure_only=False):
        # Create main container with modern styling
        main_container = self.ui_style.create_modern_frame(parent_frame, bg=parent_frame['bg'])
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Title section
        title_frame = self.ui_style.create_modern_frame(main_container, bg=parent_frame['bg'])
        title_frame.pack(fill="x", pady=(0, 5))
        title_frame.columnconfigure(0, weight=1)
        
        title_label = self.ui_style.create_modern_label(title_frame, self.json_data["labels"]["sew_db_title"], 
                                                       style='title', bg=parent_frame['bg'])
        title_label.grid(row=0, column=0, sticky="ew")
        
        help_btn = self.ui_style.create_modern_button(title_frame, self.json_data["labels"]["sew_db_help_button"], 
                                                     self._show_help_image, style='technology')
        help_btn.grid(row=0, column=1, sticky="e", padx=(5, 0))
        
        subtitle_label = self.ui_style.create_modern_label(main_container, self.json_data["labels"]["sew_db_subtitle"], 
                                                          style='subtitle', bg=parent_frame['bg'])
        subtitle_label.pack(fill="x", pady=(0, 10))
        
        # Search criteria frame
        search_container = self.ui_style.create_modern_frame(main_container, bg=self.ui_style.colors['surface'], 
                                                           relief='solid', bd=1)
        search_container.pack(fill="x", pady=(0, 10), padx=5)
        search_container_inner = self.ui_style.create_modern_frame(search_container, bg=self.ui_style.colors['surface'])
        search_container_inner.pack(padx=8, pady=8, fill='x')
        
        # Configure grid layout for search fields
        search_container_inner.columnconfigure(1, weight=1)
        search_container_inner.columnconfigure(3, weight=1)
        
        # Error code row
        self.ui_style.create_modern_label(search_container_inner, self.json_data["labels"]["sew_db_error_code_label"], 
                                         bold=True, bg=self.ui_style.colors['surface']).grid(
                                             row=0, column=0, sticky="w", pady=4, padx=(0, 5))
                                             
        self.sew_error_code_entry = self.ui_style.create_modern_entry(search_container_inner, width=12)
        self.sew_error_code_entry.grid(row=0, column=1, sticky="ew", pady=4, padx=(0, 10))
        
        # Suberror code field
        self.ui_style.create_modern_label(search_container_inner, self.json_data["labels"]["sew_db_suberror_code_label"], 
                                         bold=True, bg=self.ui_style.colors['surface']).grid(
                                             row=0, column=2, sticky="w", pady=4, padx=(0, 5))
                                             
        self.sew_suberror_code_entry = self.ui_style.create_modern_entry(search_container_inner, width=12)
        self.sew_suberror_code_entry.grid(row=0, column=3, sticky="ew", pady=4)
        
        # Error designation field
        self.ui_style.create_modern_label(search_container_inner, self.json_data["labels"]["sew_db_error_designation_label"], 
                                         bold=True, bg=self.ui_style.colors['surface']).grid(
                                             row=1, column=0, sticky="w", pady=4, padx=(0, 5))
                                             
        self.sew_error_designation_entry = self.ui_style.create_modern_entry(search_container_inner)
        self.sew_error_designation_entry.grid(row=1, column=1, columnspan=3, sticky="ew", pady=4)
        
        # Search button
        button_frame = self.ui_style.create_modern_frame(search_container_inner, bg=self.ui_style.colors['surface'])
        button_frame.grid(row=2, column=0, columnspan=4, pady=(10, 0))
        
        search_button = self.ui_style.create_modern_button(button_frame, 
                                                         self.json_data["labels"]["sew_db_search_button"], 
                                                         self.search_sew_error_codes, 
                                                         style='submit')
        search_button.pack()
        
        # Results container
        results_container = self.ui_style.create_modern_frame(main_container, bg=self.ui_style.colors['surface'], 
                                                            relief='solid', bd=1)
        results_container.pack(fill="both", expand=True, padx=5, pady=5)
        results_container_inner = self.ui_style.create_modern_frame(results_container, bg=self.ui_style.colors['surface'])
        results_container_inner.pack(padx=8, pady=8, fill='both', expand=True)
        
        results_label = self.ui_style.create_modern_label(results_container_inner, 
                                                        self.json_data["labels"]["sew_db_results_label"],
                                                        bold=True, 
                                                        bg=self.ui_style.colors['surface'])
        results_label.pack(anchor="w", pady=(0, 5))
        
        self.results_frame = self.ui_style.create_modern_frame(results_container_inner, bg=self.ui_style.colors['surface'])
        self.results_frame.pack(fill="both", expand=True, pady=(5, 0))
        
        # Bind Enter key to search
        self.sew_error_code_entry.bind("<Return>", lambda e: self.search_sew_error_codes())
        self.sew_suberror_code_entry.bind("<Return>", lambda e: self.search_sew_error_codes())
        self.sew_error_designation_entry.bind("<Return>", lambda e: self.search_sew_error_codes())
        
        # Show initial instructions
        self._show_search_instructions()
        
        # Set window dimensions if not in measure mode
        if not measure_only:
            self.root.update_idletasks()
            screen_height = self.root.winfo_screenheight()
            max_height = int(screen_height * 0.85)
            width = min(650, self.root.winfo_reqwidth())
            height = min(max_height, max(400, self.root.winfo_reqheight()))
            self._set_window_dimensions(width, height)

    def _show_help_image(self):
        """Displays the help image in a new window."""
        image_path = os.path.join(self.script_dir, "media", "SEW_MoviPro_movitools_parameters.jpg")
        try:
            help_win = tk.Toplevel(self.root)
            help_win.title(self.json_data["labels"]["sew_db_help_title"])
            help_win.transient(self.root)
            help_win.grab_set()
            help_win.resizable(False, False)
            img = Image.open(image_path)
            img = img.resize((680, 320), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(help_win, image=photo)
            img_label.image = photo
            img_label.pack()
            
            help_win.update_idletasks()
            req_width = help_win.winfo_reqwidth()
            req_height = help_win.winfo_reqheight()
            screen_width = help_win.winfo_screenwidth()
            screen_height = help_win.winfo_screenheight()
            x = (screen_width - req_width) // 2
            y = (screen_height - req_height) // 2
            help_win.geometry(f"{req_width}x{req_height}+{x}+{y}")
        except Exception as e:
            messagebox.showerror(self.json_data["labels"]["sew_db_help_error_title"], 
                               self.json_data["labels"]["sew_db_help_error_message"].format(e=e))

    def _show_search_instructions(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        instructions_frame = ttk.Frame(self.results_frame)
        instructions_frame.pack(fill="x", padx=10, pady=10)
        icon_label = ttk.Label(instructions_frame, text=self.json_data["labels"]["sew_db_search_instructions_icon"], font=("Segoe UI", 18))
        icon_label.pack(pady=(0, 5))
        title_label = ttk.Label(instructions_frame, text=self.json_data["labels"]["sew_db_search_instructions_title"], font=("Segoe UI", 11, "bold"), foreground="#2E86AB")
        title_label.pack(pady=(0, 8))
        instructions_text = self.json_data["labels"]["sew_db_search_instructions"]
        instructions_label = ttk.Label(instructions_frame, text=instructions_text, font=("Segoe UI", 9), foreground="#666666", justify="left")
        instructions_label.pack()
        
        # Resize window to fit instructions content
        self.root.update_idletasks()
        screen_height = self.root.winfo_screenheight()
        max_height = int(screen_height * 0.85)
        req_width = min(650, max(400, self.root.winfo_reqwidth()))
        req_height = min(max_height, max(400, self.root.winfo_reqheight()))
        self._set_window_dimensions(req_width, req_height)

    def _format_single_line_content(self, text):
        if not text or text.strip() == "":
            return self.json_data["labels"]["sew_db_not_specified"]
        return ' '.join(text.replace("\n", " ").replace("\n", " ").split())

    def _show_error_card(self, error_data):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        card_frame = ttk.Frame(self.results_frame)
        card_frame.pack(fill="x", padx=10, pady=10)
        header_frame = ttk.Frame(card_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        error_code_frame = ttk.Frame(header_frame)
        error_code_frame.pack(anchor="w")
        code_text = self.json_data["labels"]["sew_db_error_card_error_code_label"].format(error_code=error_data.get('error_code', 'N/A'))
        if error_data.get('suberror_code'):
            code_text += f".{error_data.get('suberror_code')}"
        ttk.Label(error_code_frame, text=code_text, font=("Segoe UI", 14, "bold"), foreground="#FFFFFF", background="#E74C3C", padding=(10, 5)).pack(side="left")
        designation_label = ttk.Label(header_frame, text=self._format_single_line_content(error_data.get('error_designation', self.json_data["labels"]["sew_db_error_card_unknown_error"])), font=("Segoe UI", 16, "bold"), foreground="#2C3E50")
        designation_label.pack(anchor="w", pady=(10, 0))
        if error_data.get('error_response'):
            response_label = ttk.Label(header_frame, text=self.json_data["labels"]["sew_db_error_card_response_label"].format(response=self._format_single_line_content(error_data.get('error_response'))), font=("Segoe UI", 11), foreground="#E67E22")
            response_label.pack(anchor="w", pady=(5, 0))
        separator = ttk.Separator(card_frame, orient="horizontal")
        separator.pack(fill="x", pady=10)
        content_frame = ttk.Frame(card_frame)
        content_frame.pack(fill="x")
        if error_data.get('possible_cause'):
            causes_frame = ttk.LabelFrame(content_frame, text=self.json_data["labels"]["sew_db_error_card_possible_causes_label"], padding=10)
            causes_frame.pack(fill="x", pady=(0, 10))
            causes_text = tk.Label(causes_frame, text=self._format_text_content(error_data.get('possible_cause', '')), font=("Segoe UI", 10), background="#FFF5F5", foreground="#2C3E50", anchor="w", justify="left")
            causes_text.pack(fill="x")
        if error_data.get('measure'):
            actions_frame = ttk.LabelFrame(content_frame, text=self.json_data["labels"]["sew_db_error_card_recommended_actions_label"], padding=10)
            actions_frame.pack(fill="x")
            actions_text = tk.Label(actions_frame, text=self._format_text_content(error_data.get('measure', '')), font=("Segoe UI", 10), background="#F0FFF4", foreground="#2C3E50", anchor="w", justify="left")
            actions_text.pack(fill="x")

    def _format_text_content(self, text):
        if not text or text.strip() == "":
            return self.json_data["labels"]["sew_db_not_specified"]
        text = text.replace("\n", "\n")
        lines = text.split("\n")
        processed_lines = []
        current_line = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("•"):
                if current_line:
                    processed_lines.append(current_line.strip())
                current_line = line
            else:
                if current_line:
                    if current_line.rstrip().endswith(('.', ':', '!', '?')):
                        processed_lines.append(current_line.strip())
                        current_line = line
                    else:
                        current_line += " " + line
                else:
                    current_line = line
        if current_line:
            processed_lines.append(current_line.strip())
        return "\n".join(processed_lines) if processed_lines else self.json_data["labels"]["sew_db_not_specified"]

    def _show_no_results(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        no_results_frame = ttk.Frame(self.results_frame)
        no_results_frame.pack(fill="x", padx=10, pady=10)
        icon_label = ttk.Label(no_results_frame, text=self.json_data["labels"]["sew_db_no_results_icon"], font=("Segoe UI", 18))
        icon_label.pack(pady=(0, 5))
        title_label = ttk.Label(no_results_frame, text=self.json_data["labels"]["sew_db_no_results_title"], font=("Segoe UI", 11, "bold"), foreground="#E74C3C")
        title_label.pack(pady=(0, 8))
        suggestions_text = self.json_data["labels"]["sew_db_no_results_suggestions"]
        suggestions_label = ttk.Label(no_results_frame, text=suggestions_text, font=("Segoe UI", 9), foreground="#666666", justify="left")
        suggestions_label.pack()

    def _display_error_code_image(self, parent_frame, image_path):
        """Display an error code reference image in the interface."""
        try:
            full_image_path = os.path.join(self.script_dir, image_path)
            if os.path.exists(full_image_path):
                img = Image.open(full_image_path)
                # Resize preserving aspect ratio with max width of 500px
                max_width = 500
                original_width, original_height = img.size
                if original_width > max_width:
                    ratio = max_width / original_width
                    new_height = int(original_height * ratio)
                    img = img.resize((max_width, new_height), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                img_label = tk.Label(parent_frame, image=photo)
                img_label.image = photo
                img_label.pack(padx=2, pady=2)
            else:
                logging.error(f"Error code image not found: {full_image_path}")
        except Exception as e:
            logging.warning(f"Failed to load error code image '{image_path}': {e}")

    def search_sew_error_codes(self):
        db_path = os.path.join(self.script_dir, "data", "errorCodesTechnologies.db")
        if not os.path.exists(db_path):
            logging.error(f"Database file not found at {db_path}")
            messagebox.showerror("Database Error", f"The database file 'errorCodesTechnologies.db' was not found in the 'data' directory. Please run the PDF processing script to generate it.")
            return

        error_code = self.sew_error_code_entry.get().strip()
        suberror_code = self.sew_suberror_code_entry.get().strip()
        error_designation = self.sew_error_designation_entry.get().strip()
        if not any([error_code, suberror_code, error_designation]):
            self._show_search_instructions()
            return
        
        db_manager = SEWDatabaseManager(db_path)
        results = db_manager.search_error_codes(error_code, suberror_code, error_designation)

        if results:
            self._show_error_card(results[0])
        else:
            self._show_no_results()
        
        # Resize window to fit the new content
        self.root.update_idletasks()
        screen_height = self.root.winfo_screenheight()
        max_height = int(screen_height * 0.85)
        req_height = min(max_height, max(400, self.root.winfo_reqheight()))
        current_width = self.root.winfo_width()
        self._set_window_dimensions(current_width, req_height)

    def _replace_variables(self, text: str) -> str:
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

    def destroy_current_view(self) -> None:
        if self.current_view:
            self.current_view.destroy()

    def show_previous_view(self) -> None:
        if self.view_stack:
            self.destroy_current_view()
            previous_view_func, previous_view_data = self.view_stack.pop()
            if previous_view_data:
                previous_view_func(previous_view_data)
            else:
                previous_view_func()

    def _open_pdf_viewer(self, url_path: str, page_number: Optional[int] = None, search_term: str = "") -> None:
        """Opens the PDF viewer to a specific page, optionally with a search term."""
        # Construct the full path to the PDF file.
        full_path = os.path.join(self.script_dir, url_path)

        if not os.path.exists(full_path):
            logging.critical(f"PDF file not found at path: {full_path}")
            messagebox.showerror("File Not Found", f"The required PDF file could not be found at:\n{full_path}")
            return

        # --- Consolidated Logging --- 
        log_message = f"Opening PDF '{url_path}'"
        if search_term:
            log_message += f" to search for: '{search_term}'."
        elif page_number is not None:
            log_message += f" to page: '{page_number}'."
        else:
            log_message += "."
        logging.debug(log_message)

        try:
            PDFViewerWindow(self.root, full_path, initial_page_identifier=page_number, search_term=search_term)
        except Exception as e:
            logging.critical(f"Failed to open PDF viewer for '{full_path}': {e}", exc_info=True)
            messagebox.showerror("PDF Viewer Error", f"An unexpected error occurred while trying to open the PDF viewer.\n\nDetails: {e}")
