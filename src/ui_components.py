"""
UI Components Module for Troubleshooting Wizard

This module contains reusable UI styling and component creation methods
for consistent application theming and modern interface elements.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable, Optional


class UIStyleManager:
    """Manages consistent styling and UI component creation for the application."""
    
    def __init__(self) -> None:
        self._configure_color_palette()
        self._configure_ttk_styles()
    
    def _configure_color_palette(self) -> None:
        """Configures modern color palette with navigation hierarchy."""
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
    
    def _configure_ttk_styles(self) -> None:
        """Configure ttk styles for elements that must use ttk."""
        style = ttk.Style()
        style.configure("Modern.TFrame", background=self.colors['background'])
        style.configure("Modern.TLabel", 
                       background=self.colors['background'], 
                       foreground=self.colors['text_primary'], 
                       font=("Segoe UI", 9))
        style.configure("ModernBold.TLabel", 
                       background=self.colors['background'], 
                       foreground=self.colors['text_primary'], 
                       font=("Segoe UI", 10, "bold"))

    def create_modern_button(self, parent: tk.Widget, text: str, command: Callable, style: str = 'technology', **kwargs: Any) -> tk.Button:
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

    def create_modern_entry(self, parent: tk.Widget, **kwargs: Any) -> tk.Entry:
        """Creates a modern entry widget with consistent styling."""
        return tk.Entry(parent, font=("Segoe UI", 10), relief="flat", bd=0,
                       highlightthickness=2, highlightcolor=self.colors['technology'],
                       bg=self.colors['surface'], fg=self.colors['text_primary'],
                       insertbackground=self.colors['text_primary'], **kwargs)

    def create_modern_label(self, parent: tk.Widget, text: str, bold: bool = False, style: str = 'normal', **kwargs: Any) -> tk.Label:
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

    def create_modern_frame(self, parent: tk.Widget, **kwargs: Any) -> tk.Frame:
        """Creates a modern frame with consistent styling."""
        bg_color = kwargs.pop('bg', self.colors['background'])
        return tk.Frame(parent, bg=bg_color, **kwargs)

    def set_window_theme(self, root_window: tk.Tk, theme: str = 'technology') -> str:
        """Sets the window background color based on theme."""
        if theme == 'technology':
            bg_color = self.colors['bg_technology']
        elif theme == 'task':
            bg_color = self.colors['bg_task']
        elif theme == 'error':
            bg_color = self.colors['bg_error']
        else:
            bg_color = self.colors['background']
        
        root_window.configure(bg=bg_color)
        return bg_color

    def create_back_button_area(self, parent_frame: tk.Frame, button_text: str, command: Callable) -> tk.Frame:
        """Creates a standardized back button area with separator."""
        back_frame = tk.Frame(parent_frame, bg=parent_frame['bg'])
        back_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        back_button = self.create_modern_button(back_frame, "← " + button_text, 
                                               command, style='technology')
        back_button.pack(anchor="w")
        
        separator = ttk.Separator(back_frame, orient="horizontal")
        separator.pack(fill="x", pady=(5, 0))
        
        return back_frame

    def create_dual_back_button_area(self, parent_frame: tk.Frame, primary_text: str, primary_command: Callable, secondary_text: str, secondary_command: Callable) -> tk.Frame:
        """Creates two back buttons on the same row with one separator below both."""
        back_frame = tk.Frame(parent_frame, bg=parent_frame['bg'])
        back_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        # Button container
        button_container = tk.Frame(back_frame, bg=parent_frame['bg'])
        button_container.pack(fill="x")
        
        # Primary back button (technology color)
        primary_button = self.create_modern_button(button_container, "← " + primary_text, 
                                                  primary_command, style='technology')
        primary_button.pack(side="left")
        
        # Secondary back button (task color)
        secondary_button = self.create_modern_button(button_container, "← " + secondary_text, 
                                                    secondary_command, style='task')
        secondary_button.pack(side="left", padx=(10, 0))
        
        # Single separator below both buttons
        separator = ttk.Separator(back_frame, orient="horizontal")
        separator.pack(fill="x", pady=(5, 0))
        
        return back_frame
