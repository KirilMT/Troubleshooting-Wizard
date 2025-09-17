import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json
import webbrowser
import time
import pyautogui

def search_pdf(fault_message, url_path):
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

def set_window_dimensions(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

class MainApplication:
    def __init__(self, root_window, initial_json_data):
        self.root = root_window
        self.root.title(initial_json_data["MainApplication"]["title"])

        # Get the window dimensions from JSON data
        self.initial_width = initial_json_data["MainApplication"]["width"]
        self.initial_height = initial_json_data["MainApplication"]["height"]
        set_window_dimensions(self.root, self.initial_width, self.initial_height)  # Center the window

        self.json_data = initial_json_data
        self.current_view = None
        self.view_stack = []  # Stack to manage view history

        self.variables = {}  # Initialize variables dictionary

        self.show_main_program()  # Show the Main Program initially

    def show_main_program(self):
        self.destroy_current_view()
        self.view_stack.clear()  # Clear the view history
        set_window_dimensions(self.root, self.initial_width, self.initial_height)

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
            set_window_dimensions(self.root, tech_width, tech_height)

        # Extract variables data for the current technology from the JSON configuration
        self.variables = tech_data

        back_button = ttk.Button(
            tech_frame,
            text="< Back to Technologies",
            command=self.show_previous_view  # Use the previous view function
        )
        back_button.pack(side="left", anchor="nw", padx=10, pady=10)  # Move to the top-left corner

        self.modify_tasks(tech_data)  # Modify and create task buttons

    def modify_tasks(self, tech_data):
        tasks = tech_data.get("tasks", [])
        for index, task_data in enumerate(tasks):
            # Extract task attributes from the task_data dictionary
            task_title = list(task_data.keys())[0]
            task_attributes = task_data[task_title]

            # Replace variables in the URL paths with their values
            task_attributes["url_path"] = self.replace_variables(task_attributes.get("url_path", ""))

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
            self.open_url(task_attributes.get("url_path"), task_attributes.get("pdf_page_number"))

    def open_url(self, url_path, pdf_page_number=None):
        # If a page number is provided, construct the URL with the page number
        if pdf_page_number is not None:
            url_with_page = self.replace_variables(f"{url_path}#page={pdf_page_number}")
            webbrowser.open(url_with_page)
        else:
            # Open the PDF with the default web browser
            url_path = self.replace_variables(url_path)
            webbrowser.open(url_path)

    def show_error_codes(self, task_attributes, tech_data):
        self.destroy_current_view()
        self.view_stack.append((self.show_technology, tech_data))

        error_codes_width = task_attributes.get("width", 800)
        error_codes_height = task_attributes.get("height", 730)
        image_path = task_attributes.get("image_path", "")

        error_codes_frame = ttk.Frame(self.root)
        error_codes_frame.pack(fill="both", expand=True)
        self.current_view = error_codes_frame

        # Center the error_codes window
        set_window_dimensions(self.root, error_codes_width, error_codes_height)

        button_frame = ttk.Frame(error_codes_frame)
        button_frame.pack(side="top", anchor="nw", padx=10, pady=10)  # Place the button frame at the top-left corner

        home_button = ttk.Button(
            button_frame,
            text="< Back to Technologies",
            command=self.show_main_program  # Navigate to the main program
        )
        home_button.pack(side="left", padx=10)  # Place "Technologies" button on the left side of the button frame

        back_button = ttk.Button(
            button_frame,
            text="< Back to Tasks",
            command=self.show_previous_view  # Use the previous view function
        )
        back_button.pack(side="left", padx=10)  # Place "Tasks" button on the left side of the button frame

        try:
            # Load and display an image
            image = Image.open(image_path)
            photo = ImageTk.PhotoImage(image)
            image_label = ttk.Label(error_codes_frame, image=photo)
            image_label.image = photo
            image_label.pack(pady=10)
        except Exception as e:
            print(f"Error loading image: {e}")

        label_frame = ttk.Frame(error_codes_frame)
        label_frame.pack(pady=10)

        label_style = ttk.Style()
        label_style.configure("Bold.TLabel", font=("Helvetica", 15, "bold"))
        ttk.Label(label_frame, text="Insert fault code/message:", style="Bold.TLabel").pack(side="left")

        entry_style = ttk.Style()
        entry_style.configure("Large.TEntry", font=("Helvetica", 16))

        search_entry = ttk.Entry(label_frame, style="Large.TEntry", width=65)
        search_entry.pack(side="left", padx=10)

        search_button_style = ttk.Style()
        search_button_style.configure("Large.TButton", font=("Helvetica", 12))
        search_button = ttk.Button(
            error_codes_frame,
            text="Search",
            command=lambda: search_pdf(search_entry.get(), task_attributes.get("url_path"))
        )
        search_button.pack(side="right", padx=10)

    def replace_variables(self, text):
        # Replace variables in double curly braces with their values from the JSON configuration
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
    with open("data.json", "r") as json_file:
        json_data = json.load(json_file)
    app = MainApplication(root, json_data)
    root.mainloop()
