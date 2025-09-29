"""UI Components Module for Troubleshooting Wizard.

This module provides a centralized system for managing the application's user interface
components, ensuring a consistent and modern look and feel. It includes the UIStyleManager
class that handles the creation and styling of all UI elements, following a cohesive
design system with a defined color palette and typography.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable


class UIStyleManager:
    """Manages consistent styling and UI component creation for the application.

    This class serves as a centralized manager for all UI-related styling and component
    creation. It maintains a consistent design language across the application by
    providing pre-styled UI components and managing the application's color scheme.

    Attributes:
        colors (dict): A dictionary containing the application's color palette with
            keys for different UI states and elements (e.g., 'technology', 'task', 'error_critical').
    """

    def __init__(self) -> None:
        """Initialize the UIStyleManager with default color palette and styles.

        This constructor sets up the initial color palette and configures the ttk styles
        that will be used throughout the application.
        """
        self._configure_color_palette()
        self._configure_ttk_styles()

    def _configure_color_palette(self) -> None:
        """Configure the application's color palette.

        Initializes the color scheme used throughout the application, including:
        - Primary action colors (technology, task, error states)
        - Text colors for different contexts
        - Background and surface colors
        - Hover and active state colors

        The colors are stored in the instance's colors dictionary for easy access.
        """
        self.colors = {
            "technology": "#4A90E2",  # Blue for technology buttons
            "technology_hover": "#357ABD",
            "task": "#6C5CE7",  # Purple for task buttons
            "task_hover": "#5A4FCF",
            "error_critical": "#FFB366",  # Lighter orange for error codes
            "error_critical_hover": "#FF9F4D",
            "submit": "#00B894",  # Green for submit buttons
            "submit_hover": "#00A085",
            "secondary": "#B0B0B0",  # Gray for back buttons
            "secondary_hover": "#909090",
            "text_primary": "#333333",
            "text_secondary": "#666666",
            "text_light": "#FFFFFF",
            "text_error": "#D63031",  # Red text for error buttons
            "background": "#FAFAFA",
            "surface": "#FFFFFF",
            "border": "#E0E0E0",
            # Themed backgrounds (darker for better visibility)
            "bg_technology": "#D6E8FF",  # Medium light blue
            "bg_task": "#E6D9FF",  # Medium light purple
            "bg_error": "#FFE4C4",  # Medium light orange
        }

    def _configure_ttk_styles(self) -> None:
        """Configure ttk styles for themed widgets.

        Sets up custom styles for ttk widgets to match the application's design system.
        Currently configures styles for frames and labels with appropriate fonts and colors.
        """
        style = ttk.Style()
        style.configure("Modern.TFrame", background=self.colors["background"])
        style.configure(
            "Modern.TLabel",
            background=self.colors["background"],
            foreground=self.colors["text_primary"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "ModernBold.TLabel",
            background=self.colors["background"],
            foreground=self.colors["text_primary"],
            font=("Segoe UI", 10, "bold"),
        )

    def create_modern_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable,
        style: str = "technology",
        **kwargs: Any,
    ) -> tk.Button:
        """Create a modern flat button with consistent styling.

        Creates a button with a flat design, hover effects, and consistent padding.
        The button's appearance is determined by the specified style.

        Args:
            parent: The parent widget that will contain this button.
            text: The text to display on the button.
            command: The callback function to execute when the button is clicked.
            style: The style of the button. Must be one of: 'technology', 'task',
                   'error_critical', 'submit', or 'secondary'. Defaults to 'technology'.
            **kwargs: Additional keyword arguments to pass to the tkinter Button constructor.

        Returns:
            A configured tkinter Button widget with the specified style and properties.

        Example:
            >>> style_manager = UIStyleManager()
            >>> button = style_manager.create_modern_button(
            ...     root, "Click Me", lambda: print("Clicked"), style="submit")
            >>> button.pack()
        """
        font_weight = "normal"

        if style == "technology":
            bg, fg, hover_bg = (
                self.colors["technology"],
                self.colors["text_light"],
                self.colors["technology_hover"],
            )
        elif style == "task":
            bg, fg, hover_bg = (
                self.colors["task"],
                self.colors["text_light"],
                self.colors["task_hover"],
            )
        elif style == "error_critical":
            bg, fg, hover_bg = (
                self.colors["error_critical"],
                self.colors["text_error"],
                self.colors["error_critical_hover"],
            )
            font_weight = "bold"
        elif style == "submit":
            bg, fg, hover_bg = (
                self.colors["submit"],
                self.colors["text_light"],
                self.colors["submit_hover"],
            )
        elif style == "secondary":
            bg, fg, hover_bg = (
                self.colors["secondary"],
                self.colors["text_primary"],
                self.colors["secondary_hover"],
            )
        else:
            bg, fg, hover_bg = (
                self.colors["surface"],
                self.colors["text_primary"],
                self.colors["border"],
            )

        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, font_weight),
            fg=fg,
            bg=bg,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            activebackground=hover_bg,
            activeforeground=fg,
            cursor="hand2",
            **kwargs,
        )

    def create_modern_entry(self, parent: tk.Widget, **kwargs: Any) -> tk.Entry:
        """Create a modern entry widget with consistent styling.

        Creates a text entry field with a clean, flat design that matches the application's
        design system. The entry includes subtle visual feedback on focus.

        Args:
            parent: The parent widget that will contain this entry.
            **kwargs: Additional keyword arguments to pass to the tkinter Entry constructor.

        Returns:
            A configured tkinter Entry widget with modern styling.

        Example:
            >>> style_manager = UIStyleManager()
            >>> entry = style_manager.create_modern_entry(root, width=30)
            >>> entry.pack(pady=10)
        """
        return tk.Entry(
            parent,
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightcolor=self.colors["technology"],
            bg=self.colors["surface"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            **kwargs,
        )

    def create_modern_label(
        self, parent: tk.Widget, text: str, bold: bool = False, style: str = "normal", **kwargs: Any
    ) -> tk.Label:
        """Create a modern label with consistent styling.

        Creates a text label with the application's standard typography and colors.
        Supports different styles like 'title', 'subtitle', and 'normal'.

        Args:
            parent: The parent widget that will contain this label.
            text: The text to display in the label.
            bold: Whether to use bold font weight. Defaults to False.
            style: The style of the label. Can be 'title', 'subtitle', or 'normal'.
            **kwargs: Additional keyword arguments to pass to the tkinter Label constructor.

        Returns:
            A configured tkinter Label widget with modern styling.

        Example:
            >>> style_manager = UIStyleManager()
            >>> label = style_manager.create_modern_label(root, "Welcome", style="title")
            >>> label.pack(pady=10)
        """
        if style == "title":
            font = ("Segoe UI", 12, "bold")
            fg = self.colors["text_primary"]
        elif style == "subtitle":
            font = ("Segoe UI", 10)
            fg = self.colors["text_secondary"]
        else:
            font_weight = "bold" if bold else "normal"
            font = ("Segoe UI", 9, font_weight)
            fg = self.colors["text_primary"]

        bg_color = kwargs.pop("bg", self.colors["background"])
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg_color, **kwargs)

    def create_modern_frame(self, parent: tk.Widget, **kwargs: Any) -> tk.Frame:
        """Create a modern frame with consistent styling.

        Creates a container widget with the application's standard background color
        and padding. Can be used to group related UI elements.

        Args:
            parent: The parent widget that will contain this frame.
            **kwargs: Additional keyword arguments to pass to the tkinter Frame constructor.

        Returns:
            A configured tkinter Frame widget with modern styling.

        Example:
            >>> style_manager = UIStyleManager()
            >>> frame = style_manager.create_modern_frame(root, padx=20, pady=20)
            >>> frame.pack(fill='both', expand=True)
        """
        bg_color = kwargs.pop("bg", self.colors["background"])
        return tk.Frame(parent, bg=bg_color, **kwargs)

    def set_window_theme(self, root_window: tk.Tk, theme: str = "technology") -> str:
        """Set the window background color based on the specified theme.

        Updates the root window's background color to match the specified theme.
        This provides visual context about the current section of the application.

        Args:
            root_window: The root tkinter window to style.
            theme: The theme to apply. Must be one of: 'technology', 'task', or 'error'.
                   Defaults to 'technology'.

        Returns:
            The background color that was applied, as a hex string.

        Example:
            >>> root = tk.Tk()
            >>> style_manager = UIStyleManager()
            >>> bg_color = style_manager.set_window_theme(root, 'task')
            >>> print(f"Background color set to: {bg_color}")
        """
        if theme == "technology":
            bg_color = self.colors["bg_technology"]
        elif theme == "task":
            bg_color = self.colors["bg_task"]
        elif theme == "error":
            bg_color = self.colors["bg_error"]
        else:
            bg_color = self.colors["background"]

        root_window.configure(bg=bg_color)
        return bg_color

    def create_back_button_area(
        self, parent_frame: tk.Frame, button_text: str, command: Callable
    ) -> tk.Frame:
        """Creates a standardized back button area with separator."""
        back_frame = tk.Frame(parent_frame, bg=parent_frame["bg"])
        back_frame.pack(fill="x", padx=5, pady=(5, 10))

        back_button = self.create_modern_button(
            back_frame, "← " + button_text, command, style="technology"
        )
        back_button.pack(anchor="w")

        separator = ttk.Separator(back_frame, orient="horizontal")
        separator.pack(fill="x", pady=(5, 0))

        return back_frame

    def create_dual_back_button_area(
        self,
        parent_frame: tk.Frame,
        primary_text: str,
        primary_command: Callable,
        secondary_text: str,
        secondary_command: Callable,
    ) -> tk.Frame:
        """Creates two back buttons on the same row with one separator below both."""
        back_frame = tk.Frame(parent_frame, bg=parent_frame["bg"])
        back_frame.pack(fill="x", padx=5, pady=(5, 10))

        # Button container
        button_container = tk.Frame(back_frame, bg=parent_frame["bg"])
        button_container.pack(fill="x")

        # Primary back button (technology color)
        primary_button = self.create_modern_button(
            button_container, "← " + primary_text, primary_command, style="technology"
        )
        primary_button.pack(side="left")

        # Secondary back button (task color)
        secondary_button = self.create_modern_button(
            button_container, "← " + secondary_text, secondary_command, style="task"
        )
        secondary_button.pack(side="left", padx=(10, 0))

        # Single separator below both buttons
        separator = ttk.Separator(back_frame, orient="horizontal")
        separator.pack(fill="x", pady=(5, 0))

        return back_frame
