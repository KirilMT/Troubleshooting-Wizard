import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import json
import os
import sqlite3
import io
import fitz  # PyMuPDF
import pdfplumber
import logging

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class PDFViewerWindow(tk.Toplevel):
    """A stable, page-by-page PDF viewer with search and navigation."""

    def __init__(self, parent, file_path, initial_page, search_term=""):
        super().__init__(parent)
        logging.info(f"--- Initializing PDFViewerWindow for file: {file_path} ---")
        self.file_path = file_path
        self.search_term = tk.StringVar(value=search_term)
        self.doc = fitz.open(file_path)
        self.total_pages = len(self.doc)
        self.current_page = initial_page - 1  # 0-indexed
        self.photo_image = None  # Keep a reference to the current page image

        self.title(f"PDF Viewer - {os.path.basename(file_path)}")

        try:
            # Maximize window for a "full screen" feel with controls
            self.state('zoomed')
        except tk.TclError:
            # Fallback for other window managers
            width = self.winfo_screenwidth()
            height = self.winfo_screenheight()
            self.geometry(f'{width}x{height}+0+0')

        # Removed self.transient(parent) and self.grab_set() to allow standard window behavior

        self._create_toolbar()
        self._create_canvas()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Defer loading to ensure the main window has time to draw itself correctly.
        self.after(100, self.initial_load)

    def initial_load(self):
        """Load the initial page and perform the initial search if a term is provided."""
        self.display_page(self.current_page, search=True)

    def _create_toolbar(self):
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Page Navigation Controls
        self.prev_page_btn = ttk.Button(toolbar, text="<< Prev Page", command=self.prev_page)
        self.prev_page_btn.pack(side=tk.LEFT, padx=5)

        self.page_label = ttk.Label(toolbar, text="")
        self.page_label.pack(side=tk.LEFT, padx=5)

        self.next_page_btn = ttk.Button(toolbar, text="Next Page >>", command=self.next_page)
        self.next_page_btn.pack(side=tk.LEFT, padx=5)

        # Go-to-page entry
        self.page_entry = ttk.Entry(toolbar, width=5)
        self.page_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.page_entry.bind("<Return>", self.go_to_page)
        go_btn = ttk.Button(toolbar, text="Go", command=self.go_to_page)
        go_btn.pack(side=tk.LEFT, padx=5)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Search Controls
        self.search_entry = ttk.Entry(toolbar, width=30, textvariable=self.search_term)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        search_btn = ttk.Button(toolbar, text="Search", command=lambda: self.display_page(self.current_page, search=True))
        search_btn.pack(side=tk.LEFT, padx=5)

        self.match_label = ttk.Label(toolbar, text="")
        self.match_label.pack(side=tk.LEFT, padx=5)

    def _create_canvas(self):
        self.canvas = tk.Canvas(self, bg="#505050") # Dark gray background
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def display_page(self, page_num, search=False):
        """Renders and displays a single page, optionally highlighting a search term."""
        if not (0 <= page_num < self.total_pages):
            logging.warning(f"Attempted to display invalid page number: {page_num}")
            return

        self.current_page = page_num
        self.canvas.delete("all")

        try:
            page = self.doc.load_page(self.current_page)

            # Highlight search term if provided
            search_term = self.search_term.get()
            match_count = 0
            if search and search_term:
                matches = page.search_for(search_term)
                match_count = len(matches)
                for inst in matches:
                    highlight = page.add_highlight_annot(inst)
                    highlight.update()
            
            self.match_label.config(text=f"{match_count} matches on this page" if search and search_term else "")

            # --- Rendering with correct aspect ratio ---
            self.update_idletasks() # Ensure canvas dimensions are current
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            page_rect = page.rect
            zoom_x = (canvas_width - 20) / page_rect.width if page_rect.width > 0 else 1
            zoom_y = (canvas_height - 20) / page_rect.height if page_rect.height > 0 else 1
            zoom = min(zoom_x, zoom_y)  # Use the smaller zoom factor to fit the page

            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            if pix.width <= 0 or pix.height <= 0:
                logging.error(f"Invalid pixmap dimensions for page {self.current_page + 1}.")
                return

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self.photo_image = ImageTk.PhotoImage(img) # Keep a reference

            # Center the image on the canvas
            x_offset = (canvas_width - pix.width) / 2
            y_offset = (canvas_height - pix.height) / 2
            self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.photo_image)

            self.update_navigation()

        except Exception as e:
            logging.critical(f"Failed to display page {self.current_page + 1}: {e}", exc_info=True)
            self.canvas.create_text(self.canvas.winfo_width()/2, 100, text=f"Error rendering page {self.current_page + 1}", fill="red", anchor="center")

    def update_navigation(self):
        """Updates the page label and button states."""
        self.page_label.config(text=f"Page {self.current_page + 1} of {self.total_pages}")
        self.prev_page_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_page_btn.config(state=tk.NORMAL if self.current_page < self.total_pages - 1 else tk.DISABLED)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.display_page(self.current_page + 1, search=True)

    def prev_page(self):
        if self.current_page > 0:
            self.display_page(self.current_page - 1, search=True)

    def go_to_page(self, event=None):
        try:
            page_num = int(self.page_entry.get())
            if 1 <= page_num <= self.total_pages:
                self.display_page(page_num - 1, search=True)
        except ValueError:
            logging.warning("Invalid page number entered.")

    def on_close(self):
        logging.info("--- Closing PDFViewerWindow ---")
        self.doc.close()
        self.destroy()


class SEWDatabaseManager:
    """Manages SEW error code database operations."""

    def __init__(self, db_path):
        self.db_path = db_path

    def search_error_codes(self, error_code=None, suberror_code=None, error_designation=None):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            conditions, params = [], []
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
                return []
            query = "SELECT * FROM sew_error_codes_detailed WHERE " + " AND ".join(conditions)
            cursor.execute(query, params)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in results]
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return []
        finally:
            if conn:
                conn.close()


class MainApplication:
    def __init__(self, root_window, initial_json_data, script_dir):
        self.root = root_window
        self.root.title(initial_json_data["MainApplication"]["title"])
        self.script_dir = script_dir
        self.initial_width = initial_json_data["MainApplication"]["width"]
        self.initial_height = initial_json_data["MainApplication"]["height"]
        self._set_window_dimensions(self.initial_width, self.initial_height)
        self.json_data = initial_json_data
        self.current_view = None
        self.view_stack = []
        self.variables = {}
        self.show_main_program()

    def _set_window_dimensions(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _search_pdf(self, fault_message, url_path):
        """Performs a live search in a PDF and launches the viewer.""" 
        absolute_path = os.path.abspath(os.path.join(self.script_dir, "..", url_path))
        if not fault_message or not fault_message.strip():
            messagebox.showwarning("Invalid Search", "Please enter a fault message to search for.")
            return
        
        if not os.path.exists(absolute_path):
            messagebox.showerror("File Not Found", f"The PDF file could not be found at: {absolute_path}")
            return

        try:
            with pdfplumber.open(absolute_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text(x_tolerance=1)
                    if text and fault_message.lower() in text.lower():
                        page_number = i + 1
                        logging.info(f"Found search term on page {page_number}. Launching viewer.")
                        PDFViewerWindow(self.root, absolute_path, page_number, fault_message)
                        return
            messagebox.showinfo("Search Not Found", f"The fault message '{fault_message}' was not found in '{os.path.basename(url_path)}'.")
        except Exception as e:
            logging.error(f"An error occurred while searching the PDF: {e}", exc_info=True)
            messagebox.showerror("PDF Error", f"An error occurred while searching the PDF: {e}")

    def show_main_program(self):
        self.destroy_current_view()
        self.view_stack.clear()
        self._set_window_dimensions(self.initial_width, self.initial_height)
        main_program_frame = ttk.Frame(self.root)
        main_program_frame.pack(fill="both", expand=True)
        self.current_view = main_program_frame
        technologies_data = self.json_data["MainApplication"]["Technologies"]
        for tech_name, tech_data in technologies_data.items():
            tech_button = ttk.Button(main_program_frame, text=tech_data.get("button_text", ""), command=lambda data=tech_data: self.show_technology(data))
            tech_button.pack(padx=10, pady=10)

    def show_technology(self, tech_data):
        self.destroy_current_view()
        self.view_stack.append((self.show_main_program, None))
        tech_width = tech_data.get("width", self.initial_width)
        tech_height = tech_data.get("height", self.initial_height)
        tech_frame = ttk.Frame(self.root)
        tech_frame.pack(fill="both", expand=True)
        self.current_view = tech_frame
        if tech_width and tech_height:
            self._set_window_dimensions(tech_width, tech_height)
        self.variables = tech_data
        back_button = ttk.Button(tech_frame, text=self.json_data["labels"]["back_to_technologies"], command=self.show_previous_view)
        back_button.pack(side="left", anchor="nw", padx=10, pady=10)
        self._modify_tasks(tech_data)

    def _modify_tasks(self, tech_data):
        tasks = tech_data.get("tasks", [])
        for index, task_data in enumerate(tasks):
            task_title = list(task_data.keys())[0]
            task_attributes = task_data[task_title]
            task_attributes["url_path"] = self._replace_variables(task_attributes.get("url_path", ""))
            style = ttk.Style()
            style.configure("Yellow.TButton", background="yellow")
            button = ttk.Button(self.current_view, text=task_title, command=lambda attrs=task_attributes, tech=tech_data: self.show_task(attrs, tech), style="Yellow.TButton" if index == 0 else None)
            button.pack(pady=10)

    def show_task(self, task_attributes, tech_data):
        task_type = task_attributes.get("task_type")
        if task_type == "error_codes":
            self.show_error_codes(task_attributes, tech_data)

    def show_error_codes(self, task_attributes, tech_data):
        self.destroy_current_view()
        self.view_stack.append((self.show_technology, tech_data))
        error_codes_width = task_attributes.get("width", 800)
        error_codes_height = task_attributes.get("height", 730)
        is_sew_technology = tech_data.get("button_text", "").lower().find("sew") != -1
        if is_sew_technology:
            temp_frame = ttk.Frame(self.root)
            temp_frame.pack_forget()
            self._show_sew_database_interface(temp_frame, measure_only=True)
            temp_frame.update_idletasks()
            req_width = temp_frame.winfo_reqwidth()
            req_height = temp_frame.winfo_reqheight()
            temp_frame.destroy()
            self._set_window_dimensions(req_width, req_height)
            error_codes_width = req_width
            error_codes_height = req_height
        error_codes_frame = ttk.Frame(self.root)
        error_codes_frame.pack(fill="both", expand=True)
        self.current_view = error_codes_frame
        self._set_window_dimensions(error_codes_width, error_codes_height)
        button_frame = ttk.Frame(error_codes_frame)
        button_frame.pack(side="top", anchor="nw", padx=10, pady=10)
        home_button = ttk.Button(button_frame, text=self.json_data["labels"]["back_to_technologies"], command=self.show_main_program)
        home_button.pack(side="left", padx=10)
        back_button = ttk.Button(button_frame, text=self.json_data["labels"]["back_to_tasks"], command=self.show_previous_view)
        back_button.pack(side="left", padx=10)
        if is_sew_technology:
            self._show_sew_database_interface(error_codes_frame)
        else:
            self._show_traditional_search_interface(error_codes_frame, task_attributes)

    def _show_traditional_search_interface(self, parent_frame, task_attributes):
        label_frame = ttk.Frame(parent_frame)
        label_frame.pack(pady=10)
        label_style = ttk.Style()
        label_style.configure("Bold.TLabel", font=("Helvetica", 15, "bold"))
        ttk.Label(label_frame, text=self.json_data["labels"]["insert_fault_code"], style="Bold.TLabel").pack(side="left")
        entry_style = ttk.Style()
        entry_style.configure("Large.TEntry", font=("Helvetica", 16))
        search_entry = ttk.Entry(label_frame, style="Large.TEntry", width=65)
        search_entry.pack(side="left", padx=10)
        search_button = ttk.Button(parent_frame, text=self.json_data["labels"]["search"], command=lambda: self._search_pdf(search_entry.get(), task_attributes.get("url_path")))
        search_button.pack(side="right", padx=10)

    def _show_sew_database_interface(self, parent_frame, measure_only=False):
        main_container = ttk.Frame(parent_frame)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        parent_frame.update_idletasks()
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill="x", pady=(0, 10))
        title_frame.columnconfigure(0, weight=1)
        title_label = ttk.Label(title_frame, text=self.json_data["labels"]["sew_db_title"], font=("Segoe UI", 18, "bold"), foreground="#2E86AB", anchor="center", justify="center")
        title_label.grid(row=0, column=0, sticky="ew")
        help_btn = ttk.Button(title_frame, text=self.json_data["labels"]["sew_db_help_button"], width=2, command=self._show_help_image, style="Help.TButton")
        help_btn.grid(row=0, column=1, sticky="e", padx=(10, 0))
        style = ttk.Style()
        style.configure("Help.TButton", font=("Segoe UI", 12, "bold"), foreground="#2E86AB")
        subtitle_label = ttk.Label(main_container, text=self.json_data["labels"]["sew_db_subtitle"], font=("Segoe UI", 10), foreground="#666666", anchor="center", justify="center")
        subtitle_label.pack(fill="x", pady=(0, 10))
        search_container = ttk.LabelFrame(main_container, text=self.json_data["labels"]["sew_db_search_criteria_label"], padding=15)
        search_container.pack(fill="x", pady=(0, 10))
        search_container.columnconfigure(1, weight=1)
        search_container.columnconfigure(3, weight=1)
        ttk.Label(search_container, text=self.json_data["labels"]["sew_db_error_code_label"], font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 10))
        self.sew_error_code_entry = ttk.Entry(search_container, width=15, font=("Segoe UI", 10))
        self.sew_error_code_entry.grid(row=0, column=1, sticky="ew", pady=8, padx=(0, 20))
        ttk.Label(search_container, text=self.json_data["labels"]["sew_db_suberror_code_label"], font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", pady=8, padx=(0, 10))
        self.sew_suberror_code_entry = ttk.Entry(search_container, width=15, font=("Segoe UI", 10))
        self.sew_suberror_code_entry.grid(row=0, column=3, sticky="ew", pady=8)
        ttk.Label(search_container, text=self.json_data["labels"]["sew_db_error_designation_label"], font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=(16, 8), padx=(0, 10))
        self.sew_error_designation_entry = ttk.Entry(search_container, font=("Segoe UI", 10))
        self.sew_error_designation_entry.grid(row=1, column=1, columnspan=3, sticky="ew", pady=(16, 8))
        button_frame = ttk.Frame(search_container)
        button_frame.grid(row=2, column=0, columnspan=4, pady=(20, 0))
        search_button = ttk.Button(button_frame, text=self.json_data["labels"]["sew_db_search_button"], command=self.search_sew_error_codes, style="Accent.TButton")
        search_button.pack()
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"))
        self.sew_error_code_entry.bind("<Return>", lambda e: self.search_sew_error_codes())
        self.sew_suberror_code_entry.bind("<Return>", lambda e: self.search_sew_error_codes())
        self.sew_error_designation_entry.bind("<Return>", lambda e: self.search_sew_error_codes())
        results_container = ttk.LabelFrame(main_container, text=self.json_data["labels"]["sew_db_results_label"], padding=15)
        results_container.pack(fill="both", expand=True, pady=(0, 10))
        self.results_frame = ttk.Frame(results_container)
        self.results_frame.pack(fill="both", expand=True)
        self._show_search_instructions()
        if not measure_only:
            self.root.update_idletasks()
            self.root.geometry("")

    def _show_help_image(self):
        image_path = os.path.join(self.script_dir, "..", "media", "SEW_MoviPro_movitools_parameters.jpg")
        if not os.path.exists(image_path):
            image_path = os.path.join(self.script_dir, "media", "SEW_MoviPro_movitools_parameters.jpg")
        try:
            help_win = tk.Toplevel(self.root)
            help_win.title(self.json_data["labels"]["sew_db_help_title"])
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
            close_btn = ttk.Button(help_win, text=self.json_data["labels"]["sew_db_help_close_button"], command=help_win.destroy)
            close_btn.pack(pady=(0, 10))
        except Exception as e:
            messagebox.showerror(self.json_data["labels"]["sew_db_help_error_title"], self.json_data["labels"]["sew_db_help_error_message"].format(e=e))
        help_win.update_idletasks()
        popup_width = help_win.winfo_width()
        popup_height = help_win.winfo_screenheight()
        screen_width = help_win.winfo_screenwidth()
        screen_height = help_win.winfo_screenheight()
        x = int((screen_width - popup_width) / 2)
        y = int((screen_height - popup_height) / 2)
        help_win.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

    def _show_search_instructions(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        instructions_frame = ttk.Frame(self.results_frame)
        instructions_frame.pack(fill="x", padx=20, pady=20)
        icon_label = ttk.Label(instructions_frame, text=self.json_data["labels"]["sew_db_search_instructions_icon"], font=("Segoe UI", 24))
        icon_label.pack(pady=(0, 10))
        title_label = ttk.Label(instructions_frame, text=self.json_data["labels"]["sew_db_search_instructions_title"], font=("Segoe UI", 14, "bold"), foreground="#2E86AB")
        title_label.pack(pady=(0, 15))
        instructions_text = self.json_data["labels"]["sew_db_search_instructions"]
        instructions_label = ttk.Label(instructions_frame, text=instructions_text, font=("Segoe UI", 10), foreground="#666666", justify="left")
        instructions_label.pack()

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
        no_results_frame.pack(fill="x", padx=20, pady=40)
        icon_label = ttk.Label(no_results_frame, text=self.json_data["labels"]["sew_db_no_results_icon"], font=("Segoe UI", 24))
        icon_label.pack(pady=(0, 10))
        title_label = ttk.Label(no_results_frame, text=self.json_data["labels"]["sew_db_no_results_title"], font=("Segoe UI", 14, "bold"), foreground="#E74C3C")
        title_label.pack(pady=(0, 15))
        suggestions_text = self.json_data["labels"]["sew_db_no_results_suggestions"]
        suggestions_label = ttk.Label(no_results_frame, text=suggestions_text, font=("Segoe UI", 10), foreground="#666666", justify="left")
        suggestions_label.pack()

    def search_sew_error_codes(self):
        if hasattr(self, 'sew_image_label') and self.sew_image_label:
            self.sew_image_label.destroy()
            self.sew_image_label = None
        error_code = self.sew_error_code_entry.get().strip()
        suberror_code = self.sew_suberror_code_entry.get().strip()
        error_designation = self.sew_error_designation_entry.get().strip()
        if not any([error_code, suberror_code, error_designation]):
            self._show_search_instructions()
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
        db_path = os.path.join(self.script_dir, "errorCodesTechnologies.db")
        db_manager = SEWDatabaseManager(db_path)
        results = db_manager.search_error_codes(error_code, suberror_code, error_designation)
        if results:
            self._show_error_card(results[0])
        else:
            self._show_no_results()
        self.root.update_idletasks()
        new_width = self.root.winfo_width()
        new_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - new_width) // 2
        y = (screen_height - new_height) // 2
        self.root.geometry(f"{new_width}x{new_height}+{x}+{y}")

    def _replace_variables(self, text):
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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file_path = os.path.join(script_dir, "data.json")
    if not os.path.exists(data_file_path):
        data_file_path = os.path.join(script_dir, "example_data.json")
    with open(data_file_path, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)
    app = MainApplication(root, json_data, script_dir)
    root.mainloop()
