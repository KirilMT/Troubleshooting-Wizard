import tkinter as tk
from tkinter import ttk
import webbrowser
import time
import pyautogui
from PIL import Image, ImageTk
import json

# Tasks:
# - Wait until pdf is loaded (I may use Selenium):
#       https://source.chromium.org/chromium/chromium/src/+/main:chrome/browser/resources/pdf/pdf_scripting_api.ts

def set_window_dimensions(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def open_url(url_path, pdf_page_number=None):
    # If a page number is provided, construct the URL with the page number
    if pdf_page_number is not None:
        url_with_page = f"{url_path}#page={pdf_page_number}"
        webbrowser.open(url_with_page)
    else:
        # Open the PDF with the default web browser
        webbrowser.open(url_path)


class ErrorCodes:
    def __init__(self, title, width, height, url_path, image_path, url_wait_time, task_attributes=None):
        self.root = tk.Tk()
        self.root.title(title)
        set_window_dimensions(self.root, width, height)

        self.image_label = None
        self.search_entry = None
        self.photo = None
        self.url_path = url_path
        self.url_wait_time = url_wait_time  # Store the wait time for this task
        self.task_attributes = task_attributes if task_attributes is not None else {}

        # Load and display an image
        self.load_and_display_image(image_path)

        self.create_gui()

        self.root.mainloop()

    def load_and_display_image(self, image_path):
        try:
            image = Image.open(image_path)
            self.photo = ImageTk.PhotoImage(image)
            self.image_label = ttk.Label(self.root, image=self.photo)
            self.image_label.pack(pady=10)
        except Exception as e:
            print(f"Error loading image: {e}")

    def create_gui(self):
        label_frame = ttk.Frame(self.root)
        label_frame.pack(pady=10)

        label_style = ttk.Style()
        label_style.configure("Bold.TLabel", font=("Helvetica", 15, "bold"))
        ttk.Label(label_frame, text="Insert fault code/message:", style="Bold.TLabel").pack(side="left")

        entry_style = ttk.Style()
        entry_style.configure("Large.TEntry", font=("Helvetica", 16))

        self.search_entry = ttk.Entry(label_frame, style="Large.TEntry", width=65)
        self.search_entry.pack(side="left", padx=10)

        search_button_style = ttk.Style()
        search_button_style.configure("Large.TButton", font=("Helvetica", 12))
        search_button = ttk.Button(self.root, text="Search", command=self.search_pdf, style="Large.TButton")
        search_button.pack(side="right", padx=10)

    def search_pdf(self):
        fault_message = self.search_entry.get()

        # Close the window
        self.root.destroy()

        # Open the PDF file in a web browser
        pdf_page_number = self.task_attributes.get("pdf_page_number")
        open_url(self.url_path, pdf_page_number)


        # Wait for the specified wait time for the PDF file to load
        time.sleep(self.url_wait_time)

        # Simulate pressing Ctrl + F
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(1)

        # Type the search string and press Enter
        pyautogui.typewrite(fault_message)
        pyautogui.press('enter')


class Technology:
    def __init__(self, technology_name, data):
        self.image_label = None
        self.photo = None
        self.technology_name = technology_name  # Store the technology name
        w_title = data.get("title", "")
        w_width = data.get("width", 0)
        w_height = data.get("height", 0)
        tasks = data.get("tasks", [])
        self.variables = data  # Store technology-specific variables

        self.root = tk.Tk()
        self.root.title(w_title)
        set_window_dimensions(self.root, w_width, w_height)  # Set the window dimensions

        # Define custom style for the first button with a yellow background
        style = ttk.Style()
        style.configure("Yellow.TButton", background="yellow")

        # Creation of GUI buttons to launch the tasks
        for index, task_data in enumerate(tasks):
            # Extract task attributes from the task_data dictionary
            task_title = list(task_data.keys())[0]
            task_attributes = task_data[task_title]

            # Replace variables in the URL paths with their values
            task_attributes["url_path"] = self.replace_variables(task_attributes.get("url_path", ""))

            button = ttk.Button(
                self.root,
                text=task_title,
                command=lambda attrs=task_attributes: self.launch_task(attrs),
                style="Yellow.TButton" if index == 0 else None  # Apply custom style to the first button
            )
            button.pack(pady=10)

        self.root.mainloop()

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

    def launch_task(self, task_attributes):
        # Close the current window
        self.root.destroy()

        # Extract task attributes
        task_type = task_attributes.get("task_type", "")
        if task_type == "error_codes":
            # Launch the ErrorCodes class
            self.launch_error_codes(task_attributes)
        elif task_type == "open_url":
            # Extract URL and optional page number
            url_path = task_attributes.get("url_path", "")
            pdf_page_number = task_attributes.get("pdf_page_number")

            # Launch the URL with or without the page number
            open_url(url_path, pdf_page_number)

    @staticmethod
    def launch_error_codes(task_attributes):
        # Extract attributes specific to the ErrorCodes task
        title = task_attributes.get("title")
        url_path = task_attributes.get("url_path", "")
        image_path = task_attributes.get("image_path", "")
        width = task_attributes.get("width", 800)  # Use a default value if not provided
        height = task_attributes.get("height", 730)  # Use a default value if not provided
        url_wait_time = task_attributes.get("url_wait_time", 0)

        # Create an instance of the ErrorCodes class with the extracted attributes
        ErrorCodes(
            title=title,
            width=width,  # Use the extracted width
            height=height,  # Use the extracted height
            url_path=url_path,
            image_path=image_path,
            url_wait_time=url_wait_time,
            task_attributes=task_attributes
        )


class MainProgram:
    def __init__(self, technologies_config):
        self.root = tk.Tk()
        main_app_config = technologies_config.get("MainApplication", {})
        title = main_app_config.get("title", "Troubleshooting")
        width = main_app_config.get("width", 350)
        height = main_app_config.get("height", 405)
        self.root.title(title)
        set_window_dimensions(self.root, width, height)

        # Create buttons to launch different technologies from the JSON configuration
        tech_buttons = []
        for tech_name, tech_data in technologies_config.get("MainApplication", {}).get("Technologies", {}).items():
            tech_buttons.append((tech_name, tech_data))

        for tech_name, tech_data in tech_buttons:
            tech_button = ttk.Button(
                self.root,
                text=tech_name,
                command=lambda name=tech_name, data=tech_data: self.launch_tech(name, data)
            )
            tech_button.pack(pady=10)

        self.root.mainloop()

    def launch_tech(self, tech_name, tech_data):
        # Close the main window
        self.root.destroy()

        # Create a new window for the selected technology
        Technology(tech_name, tech_data)


if __name__ == "__main__":
    # Load JSON data from the configuration file
    with open("data.json", "r") as json_file:
        json_data = json.load(json_file)

    main_program = MainProgram(json_data)
