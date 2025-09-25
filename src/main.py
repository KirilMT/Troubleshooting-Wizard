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
import webbrowser
import urllib.parse

# --- Setup Logging ---
# This is now handled by src/logging_config.py and initialized in run.py
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class PDFViewerWindow(tk.Toplevel):
    """A continuous-scrolling PDF viewer with on-demand rendering and zoom."""

    def __init__(self, parent, file_path, initial_page_identifier, search_term=""):
        super().__init__(parent)
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
        else:
            # The identifier can be a page label (string) or a physical page number (int)
            try:
                page_id_str = str(initial_page_identifier).lower().strip()
                if page_id_str in self.page_label_to_index:
                    self.initial_page = self.page_label_to_index[page_id_str]
                else:
                    # Fallback to interpreting as a physical page number
                    physical_page = int(initial_page_identifier)
                    if 1 <= physical_page <= self.total_pages:
                        self.initial_page = physical_page - 1
            except (ValueError, TypeError):
                self.initial_page = 0

        # --- Caching and Layout ---
        self.page_images = {}  # Cache for PhotoImage objects {page_num: photo_image}
        self.page_layout_info = []  # List of {'y': y_pos, 'w': width, 'h': height} for each page
        self.rendering_scheduled = False
        
        # --- Hyperlink Support ---
        self.page_links = {}  # Cache for page links {page_num: [link_objects]}
        self.current_cursor = "arrow"  # Track current cursor state
        
        # --- Text Selection Support ---
        self.text_selection_active = False
        self.selection_start_char = None  # (page_num, char_index)
        self.selection_end_char = None    # (page_num, char_index)
        self.selected_text = ""
        self.selection_rectangles = []  # Visual selection rectangles on canvas
        self.page_text_data = {}  # Cache for text data with character positions
        self.page_char_map = {}  # Maps canvas coordinates to character positions
        self.is_dragging_selection = False

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
        
        # --- Mouse Event Bindings (Hyperlinks + Text Selection) ---
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Double-Button-1>", self._on_canvas_double_click)  # Double-click word selection
        self.canvas.bind("<Triple-Button-1>", self._on_canvas_triple_click)  # Triple-click line selection
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<Button-3>", self._on_right_click)  # Right-click context menu
        
        # --- Keyboard Bindings for Text Operations ---
        self.bind("<Control-c>", self._copy_selected_text)
        self.focus_set()  # Allow keyboard events

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
        self.page_links.clear()  # Clear hyperlink cache when layout changes
        self.page_text_data.clear()  # Clear text data cache when layout changes
        self.page_char_map.clear()  # Clear character mapping cache when layout changes
        self._clear_text_selection()  # Clear any active text selection

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
                        # Highlight all instances on the page with stronger yellow color
                        for inst in page.search_for(search_term):
                            highlight = page.add_highlight_annot(inst)
                            highlight.set_colors(stroke=[1, 0.8, 0])  # Stronger yellow/orange color
                            highlight.update()
                elif search_term:
                    # Legacy behavior for initial load search before full results are compiled
                    for inst in page.search_for(search_term):
                        highlight = page.add_highlight_annot(inst)
                        highlight.set_colors(stroke=[1, 0.8, 0])  # Stronger yellow/orange color
                        highlight.update()

                pix = page.get_pixmap(matrix=transform_matrix, alpha=False)
                if pix.width > 0 and pix.height > 0:
                    photo = ImageTk.PhotoImage(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
                    self.page_images[i] = photo
                    x_offset = (canvas_width - pix.width) / 2
                    self.canvas.create_image(x_offset, page_top, anchor=tk.NW, image=photo)
                    
                    # --- Extract and cache hyperlinks for this page ---
                    self._extract_page_links(i, page, transform_matrix, x_offset, page_top)
                    
                    # --- Extract and cache text data for this page ---
                    self._extract_page_text(i, page, transform_matrix, x_offset, page_top)

    def _update_page_label(self, *args):
        """Updates the page entry widget and info label based on the page most visible in the viewport."""
        scroll_region = self.canvas.cget('scrollregion')
        if not scroll_region or not self.page_layout_info: return
        
        total_height = float(scroll_region.split(' ')[3])
        if total_height == 0: return

        canvas_height = self.canvas.winfo_height()
        
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
        """Finds all instances in the document (worker thread)."""
        search_term = self.search_term.get()
        # Perform the actual search and store results in a local variable first
        results = []
        for i in range(self.total_pages):
            page = self.doc.load_page(i)
            matches = page.search_for(search_term)
            for match in matches:
                results.append((i, match))

        # Schedule the UI update on the main thread
        self.after(0, self._update_search_ui, results)

    def _update_search_ui(self, search_results):
        """Updates the UI with search results (main thread)."""
        self.search_results = search_results
        total_matches = len(self.search_results)

        # Hide "Searching..." and show navigation
        self.search_status_label.pack_forget()
        self.search_nav_frame.pack(side=tk.LEFT, padx=5)

        if total_matches > 0:
            self.current_search_index = 0
            self._go_to_match()
        else:
            self.match_label.config(text="Not found")
            self.prev_match_btn.config(state="disabled")
            self.next_match_btn.config(state="disabled")

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

    def _extract_page_links(self, page_num, page, transform_matrix, x_offset, page_top):
        """Extract and cache hyperlinks from a PDF page."""
        try:
            links = page.get_links()
            page_links = []
            
            for link in links:
                # Transform link rectangle to canvas coordinates
                link_rect = fitz.Rect(link['from'])
                transformed_rect = link_rect.transform(transform_matrix)
                
                # Adjust for canvas positioning
                canvas_rect = {
                    'x1': transformed_rect.x0 + x_offset,
                    'y1': transformed_rect.y0 + page_top,
                    'x2': transformed_rect.x1 + x_offset,
                    'y2': transformed_rect.y1 + page_top
                }
                
                # Store link information (preserve all original link data)
                link_info = {
                    'rect': canvas_rect,
                    'kind': link.get('kind', 0),
                    'page': link.get('page', -1),
                    'uri': link.get('uri', ''),
                    'to': link.get('to', None),
                    'file': link.get('file', ''),
                    'zoom': link.get('zoom', 0),
                    'xref': link.get('xref', 0),
                    'id': link.get('id', ''),
                    'nameddest': link.get('nameddest', '')
                }
                page_links.append(link_info)
            
            self.page_links[page_num] = page_links
            
        except Exception as e:
            logging.warning(f"Failed to extract links from page {page_num}: {e}")
            self.page_links[page_num] = []



    def _handle_link_click(self, link):
        """Handle clicking on a hyperlink."""
        try:
            link_kind = link['kind']
            
            # Debug logging to understand the link structure
            logging.info(f"Link clicked - Kind: {link_kind}, Data: {link}")
            
            # Handle different link types
            if link_kind == fitz.LINK_GOTO:  # Internal page link (type 1)
                target_page = link.get('page', -1)
                if target_page >= 0 and target_page < self.total_pages:
                    logging.info(f"Navigating to internal page: {target_page + 1}")
                    self.go_to_page(target_page + 1)
                    
                    # If there's a specific destination point, scroll to it
                    if link.get('to'):
                        to_point = link['to']
                        if hasattr(to_point, 'y'):
                            self._scroll_to_point_on_page(target_page, to_point.y)
                        
            elif link_kind == fitz.LINK_URI:  # External URL link (type 2)
                uri = link.get('uri', '')
                if uri:
                    logging.info(f"Opening external URL: {uri}")
                    try:
                        # Validate and open URL
                        parsed_url = urllib.parse.urlparse(uri)
                        if parsed_url.scheme in ['http', 'https', 'mailto', 'ftp']:
                            webbrowser.open(uri)
                        else:
                            logging.warning(f"Unsupported URL scheme: {parsed_url.scheme}")
                            messagebox.showwarning("Unsupported Link", 
                                                 f"Cannot open link with scheme '{parsed_url.scheme}': {uri}")
                    except Exception as e:
                        logging.error(f"Failed to open URL {uri}: {e}")
                        messagebox.showerror("Link Error", f"Failed to open link: {uri}")
                        
            elif link_kind == fitz.LINK_GOTOR:  # Link to another document (type 3)
                logging.info(f"External document link detected: {link.get('file', 'unknown')}")
                messagebox.showinfo("External Document", 
                                  "This link points to another document. External document links are not currently supported.")
                                  
            elif link_kind == 4:  # Named destination link (common in PDFs)
                # Type 4 links often use named destinations
                if 'to' in link and link['to']:
                    to_point = link['to']
                    if hasattr(to_point, 'page') and hasattr(to_point, 'y'):
                        target_page = to_point.page
                        if target_page >= 0 and target_page < self.total_pages:
                            logging.info(f"Navigating to named destination on page: {target_page + 1}")
                            self.go_to_page(target_page + 1)
                            self._scroll_to_point_on_page(target_page, to_point.y)
                        else:
                            logging.warning(f"Invalid target page in named destination: {target_page}")
                    elif 'page' in link:
                        # Fallback: try to use page from link directly
                        target_page = link.get('page', -1)
                        if target_page >= 0 and target_page < self.total_pages:
                            logging.info(f"Navigating to page from type 4 link: {target_page + 1}")
                            self.go_to_page(target_page + 1)
                        else:
                            logging.warning(f"Invalid page in type 4 link: {target_page}")
                    else:
                        logging.warning(f"Type 4 link missing destination information: {link}")
                else:
                    logging.warning(f"Type 4 link without 'to' field: {link}")
                    
            else:
                # Try to handle unknown link types generically
                logging.info(f"Attempting to handle unknown link type {link_kind}")
                
                # Check if it has page information
                if 'page' in link:
                    target_page = link.get('page', -1)
                    if target_page >= 0 and target_page < self.total_pages:
                        logging.info(f"Generic navigation to page: {target_page + 1}")
                        self.go_to_page(target_page + 1)
                        return
                
                # Check if it has 'to' destination
                if 'to' in link and link['to']:
                    to_point = link['to']
                    if hasattr(to_point, 'page'):
                        target_page = to_point.page
                        if target_page >= 0 and target_page < self.total_pages:
                            logging.info(f"Generic navigation via 'to' field to page: {target_page + 1}")
                            self.go_to_page(target_page + 1)
                            if hasattr(to_point, 'y'):
                                self._scroll_to_point_on_page(target_page, to_point.y)
                            return
                
                logging.warning(f"Could not handle link type {link_kind}: {link}")
                
        except Exception as e:
            logging.error(f"Error handling link click: {e}")

    def _scroll_to_point_on_page(self, page_num, y_coordinate):
        """Scroll to a specific Y coordinate on a given page."""
        try:
            if 0 <= page_num < len(self.page_layout_info):
                page_layout = self.page_layout_info[page_num]
                
                # Transform the Y coordinate using current zoom
                final_zoom = self.base_zoom * self.zoom_level
                transformed_y = y_coordinate * final_zoom
                
                # Calculate target position on canvas
                target_y = page_layout['y'] + transformed_y
                
                # Center the target position in the viewport
                canvas_height = self.canvas.winfo_height()
                scroll_to_y = target_y - (canvas_height / 2)
                
                total_height = float(self.canvas.cget('scrollregion').split(' ')[3])
                if total_height > 0:
                    scroll_fraction = max(0, min(1, scroll_to_y / total_height))
                    self.canvas.yview_moveto(scroll_fraction)
                    self.after(50, self._update_page_label)
                    
        except Exception as e:
            logging.warning(f"Failed to scroll to point on page {page_num}: {e}")

    def _extract_page_text(self, page_num, page, transform_matrix, x_offset, page_top):
        """Extract and cache text data with precise character-level positioning."""
        try:
            # Use get_text with "rawdict" for most precise character positioning
            text_dict = page.get_text("rawdict")
            page_chars = []
            char_map = {}
            
            # Calculate starting global index based on previous pages
            global_char_index = 0
            for prev_page in range(page_num):
                if prev_page in self.page_text_data:
                    global_char_index += len(self.page_text_data[prev_page])
            
            for block in text_dict.get('blocks', []):
                if block.get('type') == 0:  # Text block
                    for line in block.get('lines', []):
                        line_chars = []
                        
                        for span in line.get('spans', []):
                            span_font_size = span.get('size', 12)
                            span_chars = span.get('chars', [])
                            
                            # Use individual character data from rawdict for maximum precision
                            for char_info in span_chars:
                                char = char_info.get('c', '')
                                char_bbox = char_info.get('bbox', [0, 0, 0, 0])
                                
                                if char and char_bbox:
                                    # Transform character bbox to canvas coordinates
                                    char_rect_pdf = fitz.Rect(char_bbox)
                                    char_rect_canvas = char_rect_pdf.transform(transform_matrix)
                                    
                                    canvas_bbox = {
                                        'x0': char_rect_canvas.x0 + x_offset,
                                        'y0': char_rect_canvas.y0 + page_top,
                                        'x1': char_rect_canvas.x1 + x_offset,
                                        'y1': char_rect_canvas.y1 + page_top
                                    }
                                    
                                    char_data = {
                                        'char': char,
                                        'page': page_num,
                                        'global_index': global_char_index,
                                        'bbox': canvas_bbox,
                                        'font_size': span_font_size,
                                        'line_index': len(page_chars)
                                    }
                                    
                                    line_chars.append(char_data)
                                    page_chars.append(char_data)
                                    
                                    # Create precise coordinate mapping for hit detection
                                    # Map the entire character area
                                    for y in range(int(canvas_bbox['y0']), int(canvas_bbox['y1']) + 1):
                                        for x in range(int(canvas_bbox['x0']), int(canvas_bbox['x1']) + 1):
                                            coord_key = (x, y)
                                            if coord_key not in char_map:
                                                char_map[coord_key] = global_char_index
                                    
                                    # Also map surrounding area for better hit detection
                                    center_x = int((canvas_bbox['x0'] + canvas_bbox['x1']) / 2)
                                    center_y = int((canvas_bbox['y0'] + canvas_bbox['y1']) / 2)
                                    
                                    for dy in range(-2, 3):
                                        for dx in range(-2, 3):
                                            coord_key = (center_x + dx, center_y + dy)
                                            if coord_key not in char_map:
                                                char_map[coord_key] = global_char_index
                                    
                                    global_char_index += 1
                        
            
            self.page_text_data[page_num] = page_chars
            self.page_char_map[page_num] = char_map
            
            # Debug logging
            logging.info(f"Extracted {len(page_chars)} characters from page {page_num}")
            logging.info(f"Character map has {len(char_map)} coordinate mappings")
            if page_chars:
                logging.info(f"First char: '{page_chars[0]['char']}' at {page_chars[0]['bbox']}")
                logging.info(f"Last char: '{page_chars[-1]['char']}' at {page_chars[-1]['bbox']}")
            
        except Exception as e:
            logging.error(f"Failed to extract text using rawdict from page {page_num}: {e}")
            # Fallback to dict method if rawdict fails
            try:
                logging.info(f"Falling back to dict method for page {page_num}")
                self._extract_page_text_fallback(page_num, page, transform_matrix, x_offset, page_top)
            except Exception as e2:
                logging.error(f"Fallback text extraction also failed for page {page_num}: {e2}")
                self.page_text_data[page_num] = []
                self.page_char_map[page_num] = {}
    
    def _extract_page_text_fallback(self, page_num, page, transform_matrix, x_offset, page_top):
        """Fallback text extraction method using dict format."""
        text_dict = page.get_text("dict")
        page_chars = []
        char_map = {}
        
        # Calculate starting global index
        global_char_index = 0
        for prev_page in range(page_num):
            if prev_page in self.page_text_data:
                global_char_index += len(self.page_text_data[prev_page])
        
        for block in text_dict.get('blocks', []):
            if block.get('type') == 0:  # Text block
                for line in block.get('lines', []):
                    for span in line.get('spans', []):
                        span_text = span.get('text', '')
                        span_bbox = span.get('bbox', [0, 0, 0, 0])
                        span_font_size = span.get('size', 12)
                        
                        if span_text:
                            # Calculate character positioning within the span
                            span_width = span_bbox[2] - span_bbox[0]
                            char_width = span_width / len(span_text) if len(span_text) > 0 else 0
                            
                            for i, char in enumerate(span_text):
                                # Calculate character position within span
                                char_x0 = span_bbox[0] + (i * char_width)
                                char_x1 = char_x0 + char_width
                                
                                # Create character rectangle in PDF coordinates
                                char_rect_pdf = fitz.Rect(char_x0, span_bbox[1], char_x1, span_bbox[3])
                                char_rect_canvas = char_rect_pdf.transform(transform_matrix)
                                
                                canvas_bbox = {
                                    'x0': char_rect_canvas.x0 + x_offset,
                                    'y0': char_rect_canvas.y0 + page_top,
                                    'x1': char_rect_canvas.x1 + x_offset,
                                    'y1': char_rect_canvas.y1 + page_top
                                }
                                
                                char_data = {
                                    'char': char,
                                    'page': page_num,
                                    'global_index': global_char_index,
                                    'bbox': canvas_bbox,
                                    'font_size': span_font_size,
                                    'line_index': len(page_chars)
                                }
                                
                                page_chars.append(char_data)
                                
                                # Create coordinate mapping
                                center_x = int((canvas_bbox['x0'] + canvas_bbox['x1']) / 2)
                                center_y = int((canvas_bbox['y0'] + canvas_bbox['y1']) / 2)
                                
                                for dy in range(-2, 3):
                                    for dx in range(-2, 3):
                                        coord_key = (center_x + dx, center_y + dy)
                                        if coord_key not in char_map:
                                            char_map[coord_key] = global_char_index
                                
                                global_char_index += 1
        
        self.page_text_data[page_num] = page_chars
        self.page_char_map[page_num] = char_map

    def _on_canvas_click(self, event):
        """Handle mouse clicks on the canvas for hyperlinks and character-precise text selection start."""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Clear any existing text selection
        self._clear_text_selection()
        
        # Check for hyperlink clicks first
        for page_num, links in self.page_links.items():
            if page_num in self.page_images:  # Only check visible pages
                for link in links:
                    rect = link['rect']
                    if (rect['x1'] <= canvas_x <= rect['x2'] and 
                        rect['y1'] <= canvas_y <= rect['y2']):
                        self._handle_link_click(link)
                        return
        
        # Start character-precise text selection
        logging.info(f"Canvas click at ({canvas_x}, {canvas_y})")
        char_pos = self._get_character_at_position(canvas_x, canvas_y)
        logging.info(f"Character position result: {char_pos}")
        
        if char_pos is not None:
            page_num, char_index = char_pos
            self.selection_start_char = (page_num, char_index)
            self.selection_end_char = (page_num, char_index)
            self.is_dragging_selection = True
            self.text_selection_active = True
            logging.info(f"Started text selection at page {page_num}, char {char_index}")
        else:
            logging.info("No character found at click position")

    def _on_canvas_drag(self, event):
        """Handle mouse dragging for character-precise text selection."""
        if not self.is_dragging_selection or not self.selection_start_char:
            return
            
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Find character at current drag position
        char_pos = self._get_character_at_position(canvas_x, canvas_y)
        if char_pos is not None:
            page_num, char_index = char_pos
            self.selection_end_char = (page_num, char_index)
            self._update_text_selection_visual()

    def _on_canvas_release(self, event):
        """Handle mouse release to finalize character-precise text selection."""
        if not self.is_dragging_selection:
            return
            
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Find final character position
        char_pos = self._get_character_at_position(canvas_x, canvas_y)
        if char_pos is not None:
            page_num, char_index = char_pos
            self.selection_end_char = (page_num, char_index)
            self._finalize_text_selection()
        
        self.is_dragging_selection = False

    def _on_canvas_motion(self, event):
        """Handle mouse motion for proper cursor changes and drag selection."""
        if self.is_dragging_selection:
            self._on_canvas_drag(event)
            return
            
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Check if mouse is over a hyperlink first (highest priority)
        over_link = False
        for page_num, links in self.page_links.items():
            if page_num in self.page_images:  # Only check visible pages
                for link in links:
                    rect = link['rect']
                    if (rect['x1'] <= canvas_x <= rect['x2'] and 
                        rect['y1'] <= canvas_y <= rect['y2']):
                        over_link = True
                        break
            if over_link:
                break
        
        # Check if mouse is over selectable text (only if not over link)
        over_text = False
        if not over_link:
            over_text = self._is_over_text(canvas_x, canvas_y)
        
        # Debug logging for cursor behavior (every 50th motion event to avoid spam)
        if hasattr(self, '_debug_motion_counter'):
            self._debug_motion_counter += 1
        else:
            self._debug_motion_counter = 1
            
        if self._debug_motion_counter % 50 == 0:
            logging.info(f"Motion at ({canvas_x:.1f}, {canvas_y:.1f}): over_link={over_link}, over_text={over_text}")
            logging.info(f"Available pages with text data: {list(self.page_text_data.keys())}")
            if self.page_text_data:
                total_chars = sum(len(chars) for chars in self.page_text_data.values())
                logging.info(f"Total characters extracted: {total_chars}")
        
        # Update cursor based on context with proper I-beam for text
        if over_link:
            new_cursor = "hand2"  # Hand cursor for hyperlinks
        elif over_text:
            new_cursor = "xterm"  # I-beam cursor for text selection
        else:
            new_cursor = "arrow"  # Default arrow cursor
            
        if new_cursor != self.current_cursor:
            self.canvas.config(cursor=new_cursor)
            self.current_cursor = new_cursor
            logging.debug(f"Cursor changed to: {new_cursor}")

    def _on_right_click(self, event):
        """Handle right-click to show enhanced context menu."""
        if self.selected_text:
            # Create modern context menu with improved styling
            context_menu = tk.Menu(self, tearoff=0, 
                                 bg="#FFFFFF", fg="#333333",
                                 activebackground="#0078D4", activeforeground="#FFFFFF",
                                 font=("Segoe UI", 9))
            
            # Add copy option with keyboard shortcut indication
            context_menu.add_command(label="Copy                    Ctrl+C", 
                                   command=self._copy_selected_text,
                                   accelerator="")
            
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
        else:
            # Show a brief message if no text is selected
            self._show_no_selection_feedback(event.x_root, event.y_root)

    def _on_canvas_double_click(self, event):
        """Handle double-click to select entire word."""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Clear any existing selection
        self._clear_text_selection()
        
        # Find character at click position
        char_pos = self._get_character_at_position(canvas_x, canvas_y)
        if char_pos is None:
            return
            
        page_num, char_index = char_pos
        if page_num not in self.page_text_data:
            return
            
        page_chars = self.page_text_data[page_num]
        
        # Find the character data for the clicked position
        clicked_char_data = None
        for char_data in page_chars:
            if char_data['global_index'] == char_index:
                clicked_char_data = char_data
                break
                
        if not clicked_char_data:
            return
            
        # Find word boundaries by expanding from the clicked character
        word_start_idx = char_index
        word_end_idx = char_index
        
        # Expand backwards to find word start
        for char_data in reversed(page_chars):
            if char_data['global_index'] < char_index:
                if char_data['char'].isalnum() or char_data['char'] in ['_', '-']:
                    word_start_idx = char_data['global_index']
                else:
                    break
                    
        # Expand forwards to find word end
        for char_data in page_chars:
            if char_data['global_index'] > char_index:
                if char_data['char'].isalnum() or char_data['char'] in ['_', '-']:
                    word_end_idx = char_data['global_index']
                else:
                    break
                    
        # Set selection to the entire word
        self.selection_start_char = (page_num, word_start_idx)
        self.selection_end_char = (page_num, word_end_idx)
        self.text_selection_active = True
        
        # Update visual selection and finalize
        self._update_text_selection_visual()
        self._finalize_text_selection()
        
        logging.info(f"Double-click word selection: {word_start_idx} to {word_end_idx}")

    def _on_canvas_triple_click(self, event):
        """Handle triple-click to select entire line."""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Clear any existing selection
        self._clear_text_selection()
        
        # Find character at click position
        char_pos = self._get_character_at_position(canvas_x, canvas_y)
        if char_pos is None:
            return
            
        page_num, char_index = char_pos
        if page_num not in self.page_text_data:
            return
            
        page_chars = self.page_text_data[page_num]
        
        # Find the character data for the clicked position
        clicked_char_data = None
        for char_data in page_chars:
            if char_data['global_index'] == char_index:
                clicked_char_data = char_data
                break
                
        if not clicked_char_data:
            return
            
        # Find line boundaries by looking for characters with similar Y positions
        clicked_y = (clicked_char_data['bbox']['y0'] + clicked_char_data['bbox']['y1']) / 2
        line_tolerance = 5  # pixels
        
        line_start_idx = char_index
        line_end_idx = char_index
        
        # Find all characters on the same line
        line_chars = []
        for char_data in page_chars:
            char_y = (char_data['bbox']['y0'] + char_data['bbox']['y1']) / 2
            if abs(char_y - clicked_y) <= line_tolerance:
                line_chars.append(char_data)
                
        if line_chars:
            # Sort by global index to get proper order
            line_chars.sort(key=lambda c: c['global_index'])
            line_start_idx = line_chars[0]['global_index']
            line_end_idx = line_chars[-1]['global_index']
            
        # Set selection to the entire line
        self.selection_start_char = (page_num, line_start_idx)
        self.selection_end_char = (page_num, line_end_idx)
        self.text_selection_active = True
        
        # Update visual selection and finalize
        self._update_text_selection_visual()
        self._finalize_text_selection()
        
        logging.info(f"Triple-click line selection: {line_start_idx} to {line_end_idx}")

    def _get_page_at_position(self, canvas_y):
        """Get the page number at a given canvas Y position."""
        for i, layout in enumerate(self.page_layout_info):
            if layout['y'] <= canvas_y <= layout['y'] + layout['h']:
                return i
        return None

    def _get_character_at_position(self, canvas_x, canvas_y):
        """Get the character at a specific canvas position with improved precision."""
        page_num = self._get_page_at_position(canvas_y)
        if page_num is None or page_num not in self.page_text_data:
            logging.debug(f"No page found at position y={canvas_y} or no text data for page {page_num}")
            return None
        
        # Try coordinate mapping first for fast lookup
        coord_key = (int(canvas_x), int(canvas_y))
        if page_num in self.page_char_map and coord_key in self.page_char_map[page_num]:
            char_index = self.page_char_map[page_num][coord_key]
            logging.debug(f"Found character via coordinate map: page={page_num}, char_index={char_index}")
            return (page_num, char_index)
        
        # Find the closest character with improved algorithm
        best_char = None
        min_distance = float('inf')
        
        page_chars = self.page_text_data[page_num]
        logging.debug(f"Searching through {len(page_chars)} characters on page {page_num}")
        
        for char_data in page_chars:
            bbox = char_data['bbox']
            
            # Check if point is within or very close to character bounds
            within_x = bbox['x0'] <= canvas_x <= bbox['x1']
            within_y = bbox['y0'] <= canvas_y <= bbox['y1']
            
            if within_x and within_y:
                # Point is directly within character bounds
                logging.debug(f"Found character '{char_data['char']}' at exact position: {bbox}")
                return (page_num, char_data['global_index'])
            
            # Calculate distance to character center for nearby characters
            char_center_x = (bbox['x0'] + bbox['x1']) / 2
            char_center_y = (bbox['y0'] + bbox['y1']) / 2
            
            # Use weighted distance (favor horizontal proximity for text selection)
            dx = canvas_x - char_center_x
            dy = canvas_y - char_center_y
            distance = (dx * dx) + (dy * dy * 2)  # Weight vertical distance more
            
            # Only consider characters that are reasonably close
            if distance < 2500:  # Reasonable proximity threshold
                if distance < min_distance:
                    min_distance = distance
                    best_char = (page_num, char_data['global_index'])
        
        if best_char:
            logging.debug(f"Found nearest character at distance {min_distance}: page={best_char[0]}, char_index={best_char[1]}")
        else:
            logging.debug(f"No character found near position ({canvas_x}, {canvas_y})")
        
        return best_char

    def _is_over_text(self, canvas_x, canvas_y):
        """Check if the mouse position is over selectable text."""
        return self._get_character_at_position(canvas_x, canvas_y) is not None

    def _update_text_selection_visual(self):
        """Update the visual representation with precise, contiguous text selection."""
        # Clear existing selection rectangles
        for rect_id in self.selection_rectangles:
            self.canvas.delete(rect_id)
        self.selection_rectangles.clear()
        
        if not self.selection_start_char or not self.selection_end_char:
            return
        
        start_page, start_char_idx = self.selection_start_char
        end_page, end_char_idx = self.selection_end_char
        
        # Normalize selection direction (ensure start comes before end)
        if (start_page > end_page or 
            (start_page == end_page and start_char_idx > end_char_idx)):
            start_page, start_char_idx, end_page, end_char_idx = end_page, end_char_idx, start_page, start_char_idx
        
        # Create precise, contiguous selection highlighting
        self._create_precise_selection_rectangles(start_page, start_char_idx, end_page, end_char_idx)

    def _create_precise_selection_rectangles(self, start_page, start_char_idx, end_page, end_char_idx):
        """Create precise, contiguous selection rectangles that highlight exactly what's selected."""
        # Collect all characters in the selection range across all pages
        selected_chars = []
        
        for page_num in range(start_page, end_page + 1):
            if page_num not in self.page_text_data:
                continue
                
            page_chars = self.page_text_data[page_num]
            for char_data in page_chars:
                char_idx = char_data['global_index']
                
                # Include character if it's within the selection range
                if start_char_idx <= char_idx <= end_char_idx:
                    selected_chars.append(char_data)
        
        if not selected_chars:
            return
        
        # Group characters by lines for precise highlighting
        self._create_line_based_selection(selected_chars)

    def _create_line_based_selection(self, selected_chars):
        """Create precise selection rectangles grouped by text lines."""
        if not selected_chars:
            return
            
        # Sort characters by position (top to bottom, left to right)
        selected_chars.sort(key=lambda c: (c['bbox']['y0'], c['bbox']['x0']))
        
        # Group characters into lines based on vertical position
        lines = []
        current_line = []
        current_y = None
        line_tolerance = 5  # pixels
        
        for char_data in selected_chars:
            char_y = (char_data['bbox']['y0'] + char_data['bbox']['y1']) / 2
            
            if current_y is None or abs(char_y - current_y) <= line_tolerance:
                # Same line
                current_line.append(char_data)
                current_y = char_y
            else:
                # New line
                if current_line:
                    lines.append(current_line)
                current_line = [char_data]
                current_y = char_y
        
        # Add the last line
        if current_line:
            lines.append(current_line)
        
        # Create selection rectangles for each line
        for line_chars in lines:
            if line_chars:
                self._create_contiguous_line_selection(line_chars)

    def _create_contiguous_line_selection(self, line_chars):
        """Create a contiguous selection rectangle for characters on the same line."""
        if not line_chars:
            return
        
        # Sort characters by horizontal position
        line_chars.sort(key=lambda c: c['bbox']['x0'])
        
        # Group consecutive characters for precise highlighting
        char_groups = []
        current_group = []
        
        for i, char_data in enumerate(line_chars):
            if not current_group:
                current_group = [char_data]
            else:
                # Check if this character is adjacent to the previous one
                prev_char = current_group[-1]
                gap = char_data['bbox']['x0'] - prev_char['bbox']['x1']
                
                # If gap is small (within reasonable character spacing), add to current group
                if gap <= 10:  # Allow for reasonable character spacing
                    current_group.append(char_data)
                else:
                    # Gap is too large, start a new group
                    char_groups.append(current_group)
                    current_group = [char_data]
        
        # Add the last group
        if current_group:
            char_groups.append(current_group)
        
        # Create selection rectangles for each contiguous group
        for group in char_groups:
            if group:
                # Calculate bounds for this group
                min_x = min(char['bbox']['x0'] for char in group)
                max_x = max(char['bbox']['x1'] for char in group)
                min_y = min(char['bbox']['y0'] for char in group)
                max_y = max(char['bbox']['y1'] for char in group)
                
                # Create modern, semi-transparent selection rectangle
                rect_id = self.canvas.create_rectangle(
                    min_x, min_y, max_x, max_y,
                    fill="#0078D4", stipple="gray12", outline="", width=0
                )
                self.selection_rectangles.append(rect_id)

    def _highlight_characters_on_page(self, page_num, start_char_idx, end_char_idx):
        """Legacy method - now redirects to precise selection."""
        # This method is kept for compatibility but now uses the improved selection
        if page_num not in self.page_text_data:
            return
            
        page_chars = self.page_text_data[page_num]
        selected_chars = []
        
        # Find all characters in the selection range
        for char_data in page_chars:
            char_idx = char_data.get('global_index', char_data.get('index', 0))
            if start_char_idx <= char_idx <= end_char_idx:
                selected_chars.append(char_data)
        
        # Use the new precise selection method
        self._create_line_based_selection(selected_chars)

    def _create_line_selection_rectangle(self, line_chars):
        """Create a selection rectangle for a line of characters."""
        if not line_chars:
            return
        
        # Find the bounds of the selected characters in this line
        min_x = min(char['bbox']['x0'] for char in line_chars)
        max_x = max(char['bbox']['x1'] for char in line_chars)
        min_y = min(char['bbox']['y0'] for char in line_chars)
        max_y = max(char['bbox']['y1'] for char in line_chars)
        
        # Create selection rectangle with standard selection color
        rect_id = self.canvas.create_rectangle(
            min_x, min_y, max_x, max_y,
            fill="#316AC5", stipple="gray25", outline="", width=0
        )
        self.selection_rectangles.append(rect_id)

    def _finalize_text_selection(self):
        """Extract and store the precisely selected text that matches the visual selection."""
        if not self.selection_start_char or not self.selection_end_char:
            self.selected_text = ""
            return
            
        start_page, start_char_idx = self.selection_start_char
        end_page, end_char_idx = self.selection_end_char
        
        # Normalize selection direction (ensure start comes before end)
        if (start_page > end_page or 
            (start_page == end_page and start_char_idx > end_char_idx)):
            start_page, start_char_idx, end_page, end_char_idx = end_page, end_char_idx, start_page, start_char_idx
        
        # Collect all selected characters across all pages in order
        all_selected_chars = []
        
        for page_num in range(start_page, end_page + 1):
            if page_num not in self.page_text_data:
                continue
                
            page_chars = self.page_text_data[page_num]
            
            for char_data in page_chars:
                char_idx = char_data['global_index']
                if start_char_idx <= char_idx <= end_char_idx:
                    all_selected_chars.append(char_data)
        
        if not all_selected_chars:
            self.selected_text = ""
            return
        
        # Sort characters by their global index to maintain exact order
        all_selected_chars.sort(key=lambda c: c['global_index'])
        
        # Extract text exactly as it appears - no cleaning or modification
        selected_text = ''.join(char_data['char'] for char_data in all_selected_chars)
        
        # Only remove leading/trailing whitespace, preserve internal structure
        self.selected_text = selected_text.strip()
        
        logging.info(f"Extracted text ({len(self.selected_text)} chars): '{self.selected_text[:50]}{'...' if len(self.selected_text) > 50 else ''}'")

    def _clear_text_selection(self):
        """Clear the current character-precise text selection."""
        # Clear visual selection rectangles
        for rect_id in self.selection_rectangles:
            self.canvas.delete(rect_id)
        self.selection_rectangles.clear()
        
        # Reset selection state
        self.text_selection_active = False
        self.selection_start_char = None
        self.selection_end_char = None
        self.selected_text = ""
        self.is_dragging_selection = False

    def _copy_selected_text(self, event=None):
        """Copy selected text to clipboard with enhanced feedback."""
        if self.selected_text:
            self.clipboard_clear()
            self.clipboard_append(self.selected_text)
            logging.info(f"Copied {len(self.selected_text)} characters to clipboard")
            
            # Show enhanced feedback
            self.after(50, lambda: self._show_copy_feedback())
        else:
            logging.info("No text selected to copy")

    def _show_copy_feedback(self):
        """Show enhanced visual feedback that text was copied."""
        # Create a modern feedback label
        feedback_label = tk.Label(self, text="✓ Text copied to clipboard", 
                                bg="#28A745", fg="white", 
                                font=("Segoe UI", 9, "bold"), 
                                relief="flat", bd=0, padx=15, pady=8)
        feedback_label.place(relx=0.5, rely=0.05, anchor="center")
        
        # Add subtle animation effect
        def fade_out(alpha=1.0):
            if alpha > 0:
                # Gradually reduce visibility
                self.after(50, lambda: fade_out(alpha - 0.1))
            else:
                feedback_label.destroy()
        
        # Start fade out after 1.5 seconds
        self.after(1500, lambda: fade_out())

    def _show_no_selection_feedback(self, x, y):
        """Show feedback when right-clicking with no text selected."""
        # Create a temporary tooltip-style message
        tooltip = tk.Toplevel(self)
        tooltip.wm_overrideredirect(True)
        tooltip.configure(bg="#333333")
        
        label = tk.Label(tooltip, text="No text selected", 
                        bg="#333333", fg="white",
                        font=("Segoe UI", 8), padx=8, pady=4)
        label.pack()
        
        # Position near cursor
        tooltip.geometry(f"+{x+10}+{y+10}")
        
        # Auto-hide after 1 second
        self.after(1000, tooltip.destroy)


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
        self.script_dir = script_dir # This is now the project root
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
        """Configures modern styling for the application."""
        # Modern color palette with navigation hierarchy
        self.colors = {
            'technology': '#4A90E2',      # Blue for technology buttons
            'technology_hover': '#357ABD',
            'task': '#6C5CE7',            # Purple for task buttons  
            'task_hover': '#5A4FCF',
            'error_critical': '#FFB366',   # Lighter orange for error codes
            'error_critical_hover': '#FF9F4D',
            'submit': '#00B894',          # Green for submit buttons
            'submit_hover': '#00A085',
            'secondary': '#B0B0B0',       # Gray for back buttons
            'secondary_hover': '#909090',
            'text_primary': '#333333',
            'text_secondary': '#666666', 
            'text_light': '#FFFFFF',
            'text_error': '#D63031',      # Red text for error buttons
            'background': '#FAFAFA',
            'surface': '#FFFFFF',
            'border': '#E0E0E0',
            # Themed backgrounds (darker for better visibility)
            'bg_technology': '#D6E8FF',   # Medium light blue
            'bg_task': '#E6D9FF',         # Medium light purple
            'bg_error': '#FFE4C4'         # Medium light orange
        }
        
        # Configure ttk styles for elements that must use ttk
        style = ttk.Style()
        style.configure("Modern.TFrame", background=self.colors['background'])
        style.configure("Modern.TLabel", background=self.colors['background'], foreground=self.colors['text_primary'], font=("Segoe UI", 9))
        style.configure("ModernBold.TLabel", background=self.colors['background'], foreground=self.colors['text_primary'], font=("Segoe UI", 10, "bold"))

    def _create_modern_button(self, parent, text, command, style='technology', **kwargs):
        """Creates a modern flat button with consistent styling."""
        font_weight = "normal"
        
        if style == 'technology':
            bg, fg, hover_bg = self.colors['technology'], self.colors['text_light'], self.colors['technology_hover']
        elif style == 'task':
            bg, fg, hover_bg = self.colors['task'], self.colors['text_light'], self.colors['task_hover']
        elif style == 'error_critical':
            bg, fg, hover_bg = self.colors['error_critical'], self.colors['text_error'], self.colors['error_critical_hover']
            font_weight = "bold"
        elif style == 'submit':
            bg, fg, hover_bg = self.colors['submit'], self.colors['text_light'], self.colors['submit_hover']
        elif style == 'secondary':
            bg, fg, hover_bg = self.colors['secondary'], self.colors['text_primary'], self.colors['secondary_hover']
        else:
            bg, fg, hover_bg = self.colors['surface'], self.colors['text_primary'], self.colors['border']
            
        return tk.Button(parent, text=text, command=command,
                        font=("Segoe UI", 9, font_weight), fg=fg, bg=bg,
                        relief="flat", bd=0, padx=12, pady=8,
                        activebackground=hover_bg, activeforeground=fg,
                        cursor="hand2", **kwargs)

    def _create_modern_entry(self, parent, **kwargs):
        """Creates a modern entry widget with consistent styling."""
        return tk.Entry(parent, font=("Segoe UI", 10), relief="flat", bd=0,
                       highlightthickness=2, highlightcolor=self.colors['technology'],
                       bg=self.colors['surface'], fg=self.colors['text_primary'],
                       insertbackground=self.colors['text_primary'], **kwargs)

    def _create_modern_label(self, parent, text, bold=False, style='normal', **kwargs):
        """Creates a modern label with consistent styling."""
        if style == 'title':
            font = ("Segoe UI", 12, "bold")
            fg = self.colors['text_primary']
        elif style == 'subtitle':
            font = ("Segoe UI", 10)
            fg = self.colors['text_secondary']
        else:
            font_weight = "bold" if bold else "normal"
            font = ("Segoe UI", 9, font_weight)
            fg = self.colors['text_primary']
        
        bg_color = kwargs.pop('bg', self.colors['background'])
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg_color, **kwargs)

    def _create_modern_frame(self, parent, **kwargs):
        """Creates a modern frame with consistent styling."""
        bg_color = kwargs.pop('bg', self.colors['background'])
        return tk.Frame(parent, bg=bg_color, **kwargs)

    def _set_window_theme(self, theme='technology'):
        """Sets the window background color based on theme."""
        if theme == 'technology':
            bg_color = self.colors['bg_technology']
        elif theme == 'task':
            bg_color = self.colors['bg_task']
        elif theme == 'error':
            bg_color = self.colors['bg_error']
        else:
            bg_color = self.colors['background']
        
        self.root.configure(bg=bg_color)
        return bg_color

    def _create_back_button_area(self, parent_frame, button_text, command):
        """Creates a standardized back button area with separator."""
        back_frame = tk.Frame(parent_frame, bg=parent_frame['bg'])
        back_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        back_button = self._create_modern_button(back_frame, "← " + button_text, 
                                                command, style='technology')
        back_button.pack(anchor="w")
        
        separator = ttk.Separator(back_frame, orient="horizontal")
        separator.pack(fill="x", pady=(5, 0))
        
        return back_frame

    def _create_dual_back_button_area(self, parent_frame, primary_text, primary_command, secondary_text, secondary_command):
        """Creates two back buttons on the same row with one separator below both."""
        back_frame = tk.Frame(parent_frame, bg=parent_frame['bg'])
        back_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        # Button container
        button_container = tk.Frame(back_frame, bg=parent_frame['bg'])
        button_container.pack(fill="x")
        
        # Primary back button (technology color)
        primary_button = self._create_modern_button(button_container, "← " + primary_text, 
                                                   primary_command, style='technology')
        primary_button.pack(side="left")
        
        # Secondary back button (task color)
        secondary_button = self._create_modern_button(button_container, "← " + secondary_text, 
                                                     secondary_command, style='task')
        secondary_button.pack(side="left", padx=(10, 0))
        
        # Single separator below both buttons
        separator = ttk.Separator(back_frame, orient="horizontal")
        separator.pack(fill="x", pady=(5, 0))
        
        return back_frame

    def _set_window_dimensions(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def show_main_program(self):
        self.destroy_current_view()
        self.view_stack.clear()
        # Set technology theme
        bg_color = self._set_window_theme('technology')
        main_program_frame = tk.Frame(self.root, bg=bg_color)
        main_program_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.current_view = main_program_frame
        
        technologies_data = self.json_data["MainApplication"]["Technologies"]
        tech_list = list(technologies_data.items())
        
        # Create grid layout: max 10 rows per column
        for i, (tech_name, tech_data) in enumerate(tech_list):
            row = i % 10
            col = i // 10
            tech_button = self._create_modern_button(main_program_frame, tech_data.get("button_text", ""), 
                                                    lambda data=tech_data: self.show_technology(data), style='technology')
            tech_button.grid(row=row, column=col, padx=5, pady=3, sticky="ew")
            main_program_frame.columnconfigure(col, weight=1)
        
        # Dynamic sizing
        self.root.update_idletasks()
        req_width = max(200, main_program_frame.winfo_reqwidth() + 20)
        req_height = main_program_frame.winfo_reqheight() + 20
        self._set_window_dimensions(req_width, req_height)

    def show_technology(self, tech_data):
        self.destroy_current_view()
        self.view_stack.append((self.show_main_program, None))
        # Set task theme
        bg_color = self._set_window_theme('task')
        tech_frame = tk.Frame(self.root, bg=bg_color)
        tech_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.current_view = tech_frame
        self.variables = tech_data
        
        # Create standardized back button area
        self._create_back_button_area(tech_frame, self.json_data["labels"]["back_to_technologies"], self.show_previous_view)
        
        self._modify_tasks(tech_data)
        
        # Dynamic sizing
        self.root.update_idletasks()
        req_width = max(200, tech_frame.winfo_reqwidth() + 20)
        req_height = tech_frame.winfo_reqheight() + 20
        self._set_window_dimensions(req_width, req_height)

    def _modify_tasks(self, tech_data):
        tasks = tech_data.get("tasks", [])
        for index, task_data in enumerate(tasks):
            task_title = list(task_data.keys())[0]
            task_attributes = task_data[task_title]
            task_attributes["url_path"] = self._replace_variables(task_attributes.get("url_path", ""))
            # The style is now configured globally
            # Error codes button gets critical styling, others get task styling
            task_title_lower = task_title.lower()
            if 'error' in task_title_lower and ('code' in task_title_lower or 'codes' in task_title_lower):
                button_style = 'error_critical'
            else:
                button_style = 'task'
            button = self._create_modern_button(self.current_view, task_title, 
                                              lambda attrs=task_attributes, tech=tech_data: self.show_task(attrs, tech), 
                                              style=button_style)
            button.pack(pady=3)

    def show_task(self, task_attributes, tech_data):
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
                logging.warning("Task with type 'open_url' is missing a 'url_path'.")
                messagebox.showwarning("Configuration Error", "This task is configured to open a file, but the file path is missing.")

    def show_error_codes(self, task_attributes, tech_data):
        self.destroy_current_view()
        self.view_stack.append((self.show_technology, tech_data))
        # Dynamic sizing will be set after content is created
        is_sew_technology = tech_data.get("button_text", "").lower().find("sew") != -1

        # --- Robustness Check for SEW Database ---
        if is_sew_technology:
            db_path = os.path.join(self.script_dir, "data", "errorCodesTechnologies.db")
            if not os.path.exists(db_path):
                logging.error(f"Database file not found at expected path: {db_path}")
                messagebox.showerror(
                    "Database Not Found",
                    f"The SEW error code database could not be found.\n\nExpected at: {db_path}"
                )
                # Revert to the previous view since we cannot proceed
                self.show_previous_view()
                return

        # Set error theme and create frame
        bg_color = self._set_window_theme('error')
        error_codes_frame = tk.Frame(self.root, bg=bg_color)
        error_codes_frame.pack(fill="both", expand=True)
        self.current_view = error_codes_frame
        # Create dual navigation buttons
        self._create_dual_back_button_area(error_codes_frame, 
                                          self.json_data["labels"]["back_to_technologies"], self.show_main_program,
                                          self.json_data["labels"]["back_to_tasks"], self.show_previous_view)
        if is_sew_technology:
            self._show_sew_database_interface(error_codes_frame)
        else:
            self._show_traditional_search_interface(error_codes_frame, task_attributes)
        
        # Dynamic sizing after content is created
        self.root.update_idletasks()
        req_width = max(400, error_codes_frame.winfo_reqwidth() + 20)
        req_height = max(300, error_codes_frame.winfo_reqheight() + 20)
        self._set_window_dimensions(req_width, req_height)

    def _show_traditional_search_interface(self, parent_frame, task_attributes):
        # Main content area (minimal padding)
        content_frame = self._create_modern_frame(parent_frame, bg=parent_frame['bg'])
        content_frame.pack(fill='both', expand=True, padx=5)
        
        # Display the configured image if available (center-aligned)
        image_path = task_attributes.get("image_path")
        if image_path:
            image_container = self._create_modern_frame(content_frame, bg=parent_frame['bg'])
            image_container.pack()
            self._display_error_code_image(image_container, image_path)
        
        # Search input frame (center-aligned)
        input_frame = self._create_modern_frame(content_frame, bg=parent_frame['bg'])
        input_frame.pack(pady=(8, 0))
        input_frame.grid_columnconfigure(1, weight=1)
        
        search_label = self._create_modern_label(input_frame, 
                                                self.json_data["labels"]["insert_fault_code"], 
                                                style='title', bg=parent_frame['bg'])
        search_label.grid(row=0, column=0, sticky="w")
        
        search_entry = self._create_modern_entry(input_frame, width=42)
        search_entry.grid(row=0, column=1, sticky="w", padx=(10, 0), ipady=5)
        
        # Search button on new row, aligned to right edge of entry
        search_button = self._create_modern_button(input_frame, self.json_data["labels"]["search"], 
                                                  lambda: self._open_pdf_viewer(task_attributes.get("url_path"), search_term=search_entry.get()),
                                                  style='submit')
        search_button.grid(row=1, column=1, sticky="e", pady=(8, 0))

    def _show_sew_database_interface(self, parent_frame, measure_only=False):
        main_container = self._create_modern_frame(parent_frame, bg=parent_frame['bg'])
        main_container.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Modern title section
        title_frame = self._create_modern_frame(main_container, bg=parent_frame['bg'])
        title_frame.pack(fill="x", pady=(0, 15))
        title_frame.columnconfigure(0, weight=1)
        
        title_label = self._create_modern_label(title_frame, self.json_data["labels"]["sew_db_title"], 
                                               style='title', bg=parent_frame['bg'])
        title_label.grid(row=0, column=0, sticky="ew")
        
        help_btn = self._create_modern_button(title_frame, self.json_data["labels"]["sew_db_help_button"], 
                                             self._show_help_image, style='technology')
        help_btn.grid(row=0, column=1, sticky="e", padx=(10, 0))
        subtitle_label = self._create_modern_label(main_container, self.json_data["labels"]["sew_db_subtitle"], 
                                                  style='subtitle', bg=parent_frame['bg'])
        subtitle_label.pack(fill="x", pady=(0, 15))
        
        # Modern search form
        search_container = self._create_modern_frame(main_container, bg=self.colors['surface'], relief='solid', bd=1)
        search_container.pack(fill="x", pady=(0, 15), padx=5)
        
        # Form title
        form_title = self._create_modern_label(search_container, self.json_data["labels"]["sew_db_search_criteria_label"], 
                                              bold=True, bg=self.colors['surface'])
        form_title.pack(pady=(15, 10))
        
        # Form content
        form_content = self._create_modern_frame(search_container, bg=self.colors['surface'])
        form_content.pack(fill="x", padx=15, pady=(0, 15))
        form_content.columnconfigure(1, weight=1)
        form_content.columnconfigure(3, weight=1)
        
        # Error code row
        self._create_modern_label(form_content, self.json_data["labels"]["sew_db_error_code_label"], 
                                 bold=True, bg=self.colors['surface']).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 10))
        self.sew_error_code_entry = self._create_modern_entry(form_content, width=12)
        self.sew_error_code_entry.grid(row=0, column=1, sticky="ew", pady=8, padx=(0, 15), ipady=3)
        
        self._create_modern_label(form_content, self.json_data["labels"]["sew_db_suberror_code_label"], 
                                 bold=True, bg=self.colors['surface']).grid(row=0, column=2, sticky="w", pady=8, padx=(0, 10))
        self.sew_suberror_code_entry = self._create_modern_entry(form_content, width=12)
        self.sew_suberror_code_entry.grid(row=0, column=3, sticky="ew", pady=8, ipady=3)
        
        # Error designation row
        self._create_modern_label(form_content, self.json_data["labels"]["sew_db_error_designation_label"], 
                                 bold=True, bg=self.colors['surface']).grid(row=1, column=0, sticky="w", pady=8, padx=(0, 10))
        self.sew_error_designation_entry = self._create_modern_entry(form_content)
        self.sew_error_designation_entry.grid(row=1, column=1, columnspan=3, sticky="ew", pady=8, ipady=3)
        # Search button
        button_frame = self._create_modern_frame(search_container, bg=self.colors['surface'])
        button_frame.grid(row=2, column=0, columnspan=4, pady=(15, 0))
        search_button = self._create_modern_button(button_frame, self.json_data["labels"]["sew_db_search_button"], 
                                                  self.search_sew_error_codes, style='submit')
        search_button.pack(pady=(0, 10))
        
        # Bind Enter key to search
        self.sew_error_code_entry.bind("<Return>", lambda e: self.search_sew_error_codes())
        self.sew_suberror_code_entry.bind("<Return>", lambda e: self.search_sew_error_codes())
        self.sew_error_designation_entry.bind("<Return>", lambda e: self.search_sew_error_codes())
        
        # Modern results container
        results_container = self._create_modern_frame(main_container, bg=self.colors['surface'], relief='solid', bd=1)
        results_container.pack(fill="both", expand=True, padx=5)
        
        results_title = self._create_modern_label(results_container, self.json_data["labels"]["sew_db_results_label"], 
                                                 bold=True, bg=self.colors['surface'])
        results_title.pack(pady=(15, 10))
        
        self.results_frame = self._create_modern_frame(results_container, bg=self.colors['surface'])
        self.results_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self._show_search_instructions()
        if not measure_only:
            self.root.update_idletasks()
            req_width = max(400, main_container.winfo_reqwidth() + 20)
            req_height = max(300, main_container.winfo_reqheight() + 20)
            self._set_window_dimensions(req_width, req_height)

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
            messagebox.showerror(self.json_data["labels"]["sew_db_help_error_title"], self.json_data["labels"]["sew_db_help_error_message"].format(e=e))

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
                logging.warning(f"Error code image not found: {full_image_path}")
        except Exception as e:
            logging.error(f"Failed to load error code image '{image_path}': {e}")

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
        # Keep compact sizing after showing results
        self.root.update_idletasks()

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
        # Construct the full path to the PDF file.
        full_path = os.path.join(self.script_dir, url_path)

        if not os.path.exists(full_path):
            logging.error(f"PDF file not found at path: {full_path}")
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
        logging.info(log_message)

        try:
            PDFViewerWindow(self.root, full_path, initial_page_identifier=page_number, search_term=search_term)
        except Exception as e:
            logging.critical(f"Failed to open PDF viewer for '{full_path}': {e}", exc_info=True)
            messagebox.showerror("PDF Viewer Error", f"An unexpected error occurred while trying to open the PDF viewer.\n\nDetails: {e}")
