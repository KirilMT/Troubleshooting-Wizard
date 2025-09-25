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
import threading

# --- Setup Logging ---
# This is now handled by src/logging_config.py and initialized in run.py
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class PDFViewerWindow(tk.Toplevel):
    """A continuous-scrolling PDF viewer with on-demand rendering and zoom."""

    def __init__(self, parent, file_path, initial_page_identifier, search_term=""):
        super().__init__(parent)
        logging.info(f"--- Initializing PDFViewerWindow for file: {file_path} ---")
        self.file_path = file_path
        self.search_term = tk.StringVar(value=search_term)
        self.doc = fitz.open(file_path)
        self.total_pages = len(self.doc)
        self.initial_page = 0 # Default to first page

        # --- Search Results ---
        self.search_results = []
        self.current_search_index = -1

        # --- UI Variables ---
        self.page_entry_var = tk.StringVar()
        self.page_info_var = tk.StringVar()

        # --- Page Label Handling ---
        self.page_labels = []
        self.page_label_to_index = {}
        try:
            labels = []
            for i in range(self.total_pages):
                page = self.doc.load_page(i)
                label = page.get_label()
                # If a page has no explicit label, fall back to its physical page number for display.
                if not label:
                    labels.append(str(i + 1))
                else:
                    labels.append(label)
            
            self.page_labels = labels
            # Create a case-insensitive map from label to physical index for navigation.
            self.page_label_to_index = {label.lower(): i for i, label in enumerate(self.page_labels)}

        except Exception as e:
            logging.error(f"A critical error occurred while retrieving page labels: {e}. Falling back to physical numbers.")
            # Critical fallback in case of unexpected library error
            self.page_labels = [str(i + 1) for i in range(self.total_pages)]
            self.page_label_to_index = {label.lower(): i for i, label in enumerate(self.page_labels)}

        # --- Resolve Initial Page --- 
        if initial_page_identifier is None:
            # If no identifier is given, default to the very first page.
            self.initial_page = 0
            logging.info("No page identifier provided. Defaulting to first page.")
        else:
            # The identifier can be a page label (string) or a physical page number (int)
            try:
                page_id_str = str(initial_page_identifier).lower().strip()
                if page_id_str in self.page_label_to_index:
                    self.initial_page = self.page_label_to_index[page_id_str]
                    logging.info(f"Resolved page label '{page_id_str}' to physical page index {self.initial_page}.")
                else:
                    # Fallback to interpreting as a physical page number
                    physical_page = int(initial_page_identifier)
                    if 1 <= physical_page <= self.total_pages:
                        self.initial_page = physical_page - 1
            except (ValueError, TypeError):
                logging.warning(f"Could not resolve initial page identifier '{initial_page_identifier}'. Defaulting to first page.")
                self.initial_page = 0

        # --- Caching and Layout ---
        self.page_images = {}  # Cache for PhotoImage objects {page_num: photo_image}
        self.page_layout_info = []  # List of {'y': y_pos, 'w': width, 'h': height} for each page
        self.rendering_scheduled = False

        # --- Zoom Functionality ---
        self.zoom_level = 1.0
        self.base_zoom = 1.0
        self.ZOOM_INCREMENT = 0.1

        self.title(f"PDF Viewer - {os.path.basename(file_path)}")

        try:
            self.state('zoomed')
        except tk.TclError:
            width = self.winfo_screenwidth()
            height = self.winfo_screenheight()
            self.geometry(f'{width}x{height}+0+0')

        self._create_toolbar()
        self._create_canvas_with_scrollbar()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # --- Bindings ---
        self.bind("<Control-plus>", self.zoom_in)
        self.bind("<Control-equal>", self.zoom_in)
        self.bind("<Control-minus>", self.zoom_out)
        self.canvas.bind("<Control-MouseWheel>", self.handle_zoom_scroll)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel) # Changed from bind_all
        self.canvas.bind("<4>", self._on_mousewheel)
        self.canvas.bind("<5>", self._on_mousewheel)
        self.bind("<Configure>", self.on_resize)

        self.after(100, self.initial_load)

    def initial_load(self):
        """Setup the canvas layout and then perform the initial search/centering."""
        self._calculate_layout(fit_to_width=True)
        # Go to the initial page requested before searching
        self.go_to_page(self.initial_page + 1)
        if self.search_term.get():
            self.after(150, self.search_and_highlight)
        else:
            # If no search term, ensure search UI is hidden
            self.search_status_label.pack_forget()
            self.search_nav_frame.pack_forget()

    def on_resize(self, event):
        """Debounce resize events to avoid excessive re-rendering."""
        if hasattr(self, '_resize_job'):
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(300, self._perform_resize)

    def _perform_resize(self):
        """Recalculate layout and re-render visible pages on resize."""
        self._calculate_layout(fit_to_width=False) # Use False to preserve current zoom
        self._update_visible_pages()

    def _create_toolbar(self):
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # --- Page Navigation ---
        page_nav_frame = ttk.Frame(toolbar)
        page_nav_frame.pack(side=tk.LEFT, padx=10)

        self.page_entry = ttk.Entry(page_nav_frame, width=8, textvariable=self.page_entry_var, justify='center')
        self.page_entry.pack(side=tk.LEFT)
        self.page_entry.bind("<Return>", self._go_to_page_from_entry)

        self.page_info_label = ttk.Label(page_nav_frame, textvariable=self.page_info_var, anchor=tk.W)
        self.page_info_label.pack(side=tk.LEFT, padx=(5, 0))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # --- Search Controls (Grouped in a Frame) ---
        search_controls_frame = ttk.Frame(toolbar)
        search_controls_frame.pack(side=tk.LEFT, padx=5)

        self.search_entry = ttk.Entry(search_controls_frame, width=30, textvariable=self.search_term)
        self.search_entry.pack(side=tk.LEFT)
        search_btn = ttk.Button(search_controls_frame, text="Search", command=self.search_and_highlight)
        search_btn.pack(side=tk.LEFT, padx=5)

        # --- Search Navigation ---
        self.search_status_label = ttk.Label(search_controls_frame, text="Searching...")
        # Pack is handled dynamically

        search_nav_frame = ttk.Frame(search_controls_frame)
        # Pack is handled dynamically

        self.prev_match_btn = ttk.Button(search_nav_frame, text="< Prev", command=self._previous_match, state="disabled")
        self.prev_match_btn.pack(side=tk.LEFT)

        self.match_label = ttk.Label(search_nav_frame, text="")
        self.match_label.pack(side=tk.LEFT, padx=5)

        self.next_match_btn = ttk.Button(search_nav_frame, text="Next >", command=self._next_match, state="disabled")
        self.next_match_btn.pack(side=tk.LEFT)

        self.search_nav_frame = search_nav_frame # Keep a reference to it

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # --- Zoom ---
        zoom_out_btn = ttk.Button(toolbar, text="-", command=self.zoom_out, width=3)
        zoom_out_btn.pack(side=tk.LEFT, padx=2)

        self.zoom_label = ttk.Label(toolbar, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=2)

        zoom_in_btn = ttk.Button(toolbar, text="+", command=self.zoom_in, width=3)
        zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        reset_zoom_btn = ttk.Button(toolbar, text="Reset Zoom", command=self.reset_zoom)
        reset_zoom_btn.pack(side=tk.LEFT, padx=5)

    def _create_canvas_with_scrollbar(self):
        canvas_container = ttk.Frame(self)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_container, bg="#505050")
        self.v_scroll = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._on_vertical_scroll)

        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _on_vertical_scroll(self, *args):
        """Handle scrollbar movement and schedule rendering of visible pages."""
        self.v_scroll.set(*args)
        self._update_page_label()
        if not self.rendering_scheduled:
            self.rendering_scheduled = True
            self.after(100, self._update_visible_pages)

    def _get_scroll_anchor(self):
        """Gets the current page and relative position to anchor the view during resizes."""
        scroll_region = self.canvas.cget('scrollregion')
        if not scroll_region or not self.page_layout_info: return None
        
        total_height = float(scroll_region.split(' ')[3])
        if total_height == 0: return None

        canvas_height = self.canvas.winfo_height()
        y_center = (self.canvas.yview()[0] * total_height) + (canvas_height / 2)

        for i, layout in enumerate(self.page_layout_info):
            if layout['y'] <= y_center < layout['y'] + layout['h']:
                relative_pos = (y_center - layout['y']) / layout['h']
                return {'page_index': i, 'relative_pos': relative_pos}
        return None

    def _restore_scroll_anchor(self, anchor):
        """Restores the view to the given anchor after a resize/zoom."""
        if not anchor or not self.page_layout_info: return

        page_index = anchor['page_index']
        if not 0 <= page_index < len(self.page_layout_info): return

        layout = self.page_layout_info[page_index]
        new_y_center = layout['y'] + (layout['h'] * anchor['relative_pos'])

        canvas_height = self.canvas.winfo_height()
        
        # Calculate the desired scroll position to center the match
        scroll_to_y = new_y_center - (canvas_height / 2)

        total_height = float(self.canvas.cget('scrollregion').split(' ')[3])
        if total_height > 0:
            scroll_fraction = max(0, min(1, scroll_to_y / total_height))
            self.canvas.yview_moveto(scroll_fraction)
            self.after(50, self._update_page_label)

    def _calculate_layout(self, fit_to_width=False):
        """Calculate the dimensions and positions of all pages without rendering them."""
        anchor = self._get_scroll_anchor()

        self.page_layout_info.clear()
        self.canvas.delete("all")
        self.page_images.clear()

        canvas_width = self.winfo_width()

        if fit_to_width:
            first_page = self.doc.load_page(0)
            page_rect = first_page.rect
            self.base_zoom = (canvas_width - 40) / page_rect.width if page_rect.width > 0 else 1
            self.zoom_level = 1.0
        
        final_zoom = self.base_zoom * self.zoom_level
        self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
        
        transform_matrix = fitz.Matrix(final_zoom, final_zoom)
        
        y_offset = 10
        for i in range(self.total_pages):
            page = self.doc.load_page(i)
            rect = page.rect.transform(transform_matrix)
            self.page_layout_info.append({'y': y_offset, 'w': rect.width, 'h': rect.height})
            y_offset += rect.height + 10

        total_height = y_offset
        self.canvas.configure(scrollregion=(0, 0, canvas_width, total_height))

        if anchor:
            self._restore_scroll_anchor(anchor)

    def _update_visible_pages(self):
        """Render and display only the pages currently visible on the canvas."""
        self.rendering_scheduled = False
        canvas_height = self.canvas.winfo_height()
        canvas_width = self.canvas.winfo_width()
        
        scroll_region = self.canvas.cget('scrollregion')
        if not scroll_region: return
        total_height = float(scroll_region.split(' ')[3])

        y_top = self.canvas.yview()[0] * total_height
        y_bottom = y_top + canvas_height

        search_term = self.search_term.get()
        final_zoom = self.base_zoom * self.zoom_level
        transform_matrix = fitz.Matrix(final_zoom, final_zoom)

        for i, layout in enumerate(self.page_layout_info):
            page_top = layout['y']
            page_bottom = page_top + layout['h']

            if page_bottom > y_top and page_top < y_bottom and i not in self.page_images:
                page = self.doc.load_page(i)
                
                # --- Highlighting Logic ---
                # Clear any previous annotations before re-rendering
                annots = page.annots()
                if annots: [page.delete_annot(a) for a in annots]

                # If there's an active search, highlight the current match if it's on this page
                if self.search_results and self.current_search_index != -1:
                    current_match_page_idx, _ = self.search_results[self.current_search_index]
                    if i == current_match_page_idx:
                        # Highlight all instances on the page, but we've navigated to one
                        for inst in page.search_for(search_term):
                            page.add_highlight_annot(inst)
                elif search_term:
                    # Legacy behavior for initial load search before full results are compiled
                    for inst in page.search_for(search_term):
                        page.add_highlight_annot(inst)

                pix = page.get_pixmap(matrix=transform_matrix, alpha=False)
                if pix.width > 0 and pix.height > 0:
                    photo = ImageTk.PhotoImage(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
                    self.page_images[i] = photo
                    x_offset = (canvas_width - pix.width) / 2
                    self.canvas.create_image(x_offset, page_top, anchor=tk.NW, image=photo)

    def _update_page_label(self, *args):
        """Updates the page entry widget and info label based on the page most visible in the viewport."""
        scroll_region = self.canvas.cget('scrollregion')
        if not scroll_region or not self.page_layout_info: return
        
        total_height = float(scroll_region.split(' ')[3])
        if total_height == 0: return

        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 1: return  # Avoid calculation before window is fully rendered

        # Determine the top and bottom of the current viewport
        y_top = self.canvas.yview()[0] * total_height
        y_bottom = y_top + canvas_height

        max_visible_height = -1
        current_page_idx = 0

        # Find the page with the largest visible area in the viewport
        for i, layout in enumerate(self.page_layout_info):
            page_top = layout['y']
            page_bottom = page_top + layout['h']

            visible_height = max(0, min(page_bottom, y_bottom) - max(page_top, y_top))

            if visible_height > max_visible_height:
                max_visible_height = visible_height
                current_page_idx = i
        
        current_page_num = current_page_idx + 1

        # Update the info label with physical page number, e.g., "(14 / 130)"
        self.page_info_var.set(f"({current_page_num} / {self.total_pages})")
        
        # Update the entry box with the logical page label, but only if not being edited.
        if self.focus_get() != self.page_entry:
            display_label = self.page_labels[current_page_idx]
            self.page_entry_var.set(display_label)

    def zoom_in(self, event=None):
        self.zoom_level += self.ZOOM_INCREMENT
        self._calculate_layout(fit_to_width=False)
        self._update_visible_pages()

    def zoom_out(self, event=None):
        self.zoom_level = max(0.1, self.zoom_level - self.ZOOM_INCREMENT) # Allow zooming out, with a minimum limit
        self._calculate_layout(fit_to_width=False)
        self._update_visible_pages()

    def reset_zoom(self, event=None):
        self._calculate_layout(fit_to_width=True)
        self._update_visible_pages()

    def handle_zoom_scroll(self, event):
        if event.delta > 0: self.zoom_in()
        else: self.zoom_out()

    def _go_to_page_from_entry(self, event=None):
        """Scrolls to the page based on the logical label or physical number in the entry widget."""
        entry_value = self.page_entry_var.get().strip()
        page_to_go = -1

        # Try to match the entry to a logical page label (case-insensitive).
        if entry_value.lower() in self.page_label_to_index:
            page_to_go = self.page_label_to_index[entry_value.lower()] + 1
        else:
            # If not a label, try to interpret it as a physical page number.
            try:
                page_to_go = int(entry_value)
            except ValueError:
                pass  # Input is not a valid label or number.

        if 1 <= page_to_go <= self.total_pages:
            self.go_to_page(page_to_go)
        else:
            # If input is invalid, show a warning and revert the entry.
            messagebox.showwarning("Invalid Page", f"'{entry_value}' is not a valid page label or number.")
            self._update_page_label()

        self.canvas.focus_set()

    def go_to_page(self, page_num):
        """Scrolls the canvas to the top of the given physical page number."""
        if 1 <= page_num <= self.total_pages and self.page_layout_info:
            y_pos = self.page_layout_info[page_num - 1]['y']
            total_height = float(self.canvas.cget('scrollregion').split(' ')[3])
            if total_height > 0:
                self.canvas.yview_moveto(y_pos / total_height)
                self.after(50, self._update_page_label) # Ensure labels update after the jump.
        else:
            self._update_page_label()

    def search_and_highlight(self):
        """Finds all matches, stores them, and navigates to the first one."""
        self.search_results.clear()
        self.current_search_index = -1

        search_term = self.search_term.get()
        if not search_term:
            self.search_status_label.pack_forget()
            self.search_nav_frame.pack_forget()
            self.match_label.config(text="")
            self.prev_match_btn.config(state="disabled")
            self.next_match_btn.config(state="disabled")
            self._update_visible_pages()
            return

        # Show searching status
        self.search_nav_frame.pack_forget()
        self.search_status_label.pack(side=tk.LEFT, padx=5)
        self.update_idletasks()

        # Perform search in a separate thread
        search_thread = threading.Thread(target=self._perform_search)
        search_thread.start()

    def _perform_search(self):
        """Finds all instances in the document."""
        search_term = self.search_term.get()
        self.search_results = []
        for i in range(self.total_pages):
            page = self.doc.load_page(i)
            matches = page.search_for(search_term)
            for match in matches:
                self.search_results.append((i, match))

        total_matches = len(self.search_results)
        if total_matches > 0:
            self.current_search_index = 0
            self._go_to_match()
        else:
            self.match_label.config(text="Not found")
            self.prev_match_btn.config(state="disabled")
            self.next_match_btn.config(state="disabled")

        # Hide "Searching..." and show navigation
        self.search_status_label.pack_forget()
        self.search_nav_frame.pack(side=tk.LEFT, padx=5)

        self._update_visible_pages()

    def _go_to_match(self):
        """Scrolls the canvas to center the current search match."""
        if not self.search_results or self.current_search_index == -1:
            return

        page_idx, match_rect = self.search_results[self.current_search_index]
        page_layout = self.page_layout_info[page_idx]

        # Calculate zoom and transformation
        final_zoom = self.base_zoom * self.zoom_level
        transform_matrix = fitz.Matrix(final_zoom, final_zoom)
        transformed_rect = match_rect.transform(transform_matrix)

        # Calculate the vertical center of the match on the canvas
        match_center_y = page_layout['y'] + (transformed_rect.y0 + transformed_rect.y1) / 2

        self.update_idletasks()
        canvas_height = self.canvas.winfo_height()
        
        # Calculate the desired scroll position to center the match
        scroll_to_y = match_center_y - (canvas_height / 2)

        total_height = float(self.canvas.cget('scrollregion').split(' ')[3])
        if total_height > 0:
            scroll_fraction = max(0, min(1, scroll_to_y / total_height))
            self.canvas.yview_moveto(scroll_fraction)

        # Update UI elements
        total_matches = len(self.search_results)
        self.match_label.config(text=f"({self.current_search_index + 1}/{total_matches})")
        self.prev_match_btn.config(state="normal" if self.current_search_index > 0 else "disabled")
        self.next_match_btn.config(state="normal" if self.current_search_index < total_matches - 1 else "disabled")

        self.after(50, self._update_visible_pages)  # Re-render after scrolling

    def _next_match(self):
        """Navigate to the next search result."""
        if self.search_results and self.current_search_index < len(self.search_results) - 1:
            self.current_search_index += 1
            self._go_to_match()

    def _previous_match(self):
        """Navigate to the previous search result."""
        if self.search_results and self.current_search_index > 0:
            self.current_search_index -= 1
            self._go_to_match()

    def _on_mousewheel(self, event):
        if event.num == 4: delta = -1
        elif event.num == 5: delta = 1
        elif event.delta > 0: delta = -1
        elif event.delta < 0: delta = 1
        else: delta = -1 * int(event.delta / 120)
        self.canvas.yview_scroll(delta, "units")

    def on_close(self):
        logging.info("--- Closing PDFViewerWindow ---")
        self.doc.close()
        self.destroy()


class SEWDatabaseManager:
    """Manages SEW error code database operations."""

    def __init__(self, db_path):
        self.db_path = db_path

    def search_error_codes(self, error_code=None, suberror_code=None, error_designation=None):
        if not os.path.exists(self.db_path):
            logging.error(f"Database file not found at {self.db_path}")
            return []
        
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
        self._configure_styles() # Centralized style configuration
        self.show_main_program()

    def _configure_styles(self):
        """Configures all ttk styles for the application."""
        style = ttk.Style()
        style.configure("Yellow.TButton", background="yellow")
        style.configure("Bold.TLabel", font=("Helvetica", 15, "bold"))
        style.configure("Large.TEntry", font=("Helvetica", 16))
        style.configure("Help.TButton", font=("Segoe UI", 12, "bold"), foreground="#2E86AB")
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"))

    def _set_window_dimensions(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

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
            # The style is now configured globally
            button = ttk.Button(self.current_view, text=task_title, command=lambda attrs=task_attributes, tech=tech_data: self.show_task(attrs, tech), style="Yellow.TButton" if index == 0 else None)
            button.pack(pady=10)

    def show_task(self, task_attributes, tech_data):
        task_type = task_attributes.get("task_type")
        if task_type == "error_codes":
            self.show_error_codes(task_attributes, tech_data)
        elif task_type == "open_url":
            url_path = task_attributes.get("url_path")
            # Get page identifier. If not present, it will be None.
            page_identifier = task_attributes.get("pdf_page_number") 
            if url_path:
                logging.info(f"Opening PDF '{url_path}' with page identifier '{page_identifier}'.")
                self._open_pdf_viewer(url_path, page_number=page_identifier)
            else:
                logging.warning("Task with type 'open_url' is missing a 'url_path'.")
                messagebox.showwarning("Configuration Error", "This task is configured to open a file, but the file path is missing.")

    def show_error_codes(self, task_attributes, tech_data):
        self.destroy_current_view()
        self.view_stack.append((self.show_technology, tech_data))
        error_codes_width = task_attributes.get("width", 800)
        error_codes_height = task_attributes.get("height", 730)
        is_sew_technology = tech_data.get("button_text", "").lower().find("sew") != -1

        # --- Robustness Check for SEW Database ---
        if is_sew_technology:
            db_path = os.path.join(self.script_dir, "errorCodesTechnologies.db")
            if not os.path.exists(db_path):
                logging.error(f"SEW database not found at expected path: {db_path}")
                messagebox.showerror(
                    "Database Not Found",
                    f"The SEW error code database could not be found.\n\nExpected at: {db_path}"
                )
                # Revert to the previous view since we cannot proceed
                self.show_previous_view()
                return

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
        # Styles are now configured globally
        ttk.Label(label_frame, text=self.json_data["labels"]["insert_fault_code"], style="Bold.TLabel").pack(side="left")
        search_entry = ttk.Entry(label_frame, style="Large.TEntry", width=65)
        search_entry.pack(side="left", padx=10)
        search_button = ttk.Button(parent_frame, text=self.json_data["labels"]["search"], command=lambda: self._open_pdf_viewer(task_attributes.get("url_path"), search_term=search_entry.get()))
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
        # Styles are now configured globally
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
        # Styles are now configured globally
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
        db_path = os.path.join(self.script_dir, "errorCodesTechnologies.db")
        if not os.path.exists(db_path):
            logging.error(f"Database file not found at {db_path}")
            messagebox.showerror("Database Error", f"The database file 'errorCodesTechnologies.db' was not found in the 'src' directory. Please run the PDF processing script to generate it.")
            return

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

    def _open_pdf_viewer(self, url_path, page_number=None, search_term=""):
        """Opens the PDF viewer to a specific page, optionally with a search term."""
        absolute_path = os.path.abspath(os.path.join(self.script_dir, "..", url_path))
        
        if not os.path.exists(absolute_path):
            messagebox.showerror("File Not Found", f"The PDF file could not be found at: {absolute_path}")
            return

        try:
            logging.info(f"Launching viewer for '{absolute_path}' with page identifier '{page_number}' and search term '{search_term}'.")
            PDFViewerWindow(self.root, absolute_path, page_number, search_term)

        except Exception as e:
            logging.error(f"An error occurred while opening the PDF: {e}", exc_info=True)
            messagebox.showerror("PDF Error", f"An error occurred while opening the PDF: {e}")
