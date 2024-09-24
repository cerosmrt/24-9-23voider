import os
import sys
import tkinter as tk
from tkinter import messagebox, Canvas, Entry, font
import random
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from get_random_line import get_random_line


class VoiderInterface:
    def __init__(self, root, void_dir):
        self.root = root
        self.void_dir = void_dir
        self.void_file_path = os.path.join(void_dir, '0.txt')

        self.root.title("Voider")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.5)  # Set the opacity to 70%

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Subtract margin for aesthetics
        thickness = 10

        # Create a canvas widget with no border
        self.canvas = Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Calculate circle center coordinates
        center_x = screen_width // 2
        center_y = screen_height // 2

        # Create the white circle outline
        radius = min(screen_width, screen_height) // 2 - thickness - 25
        self.canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, outline="white", width=thickness)

        # Calculate the circle's diameter
        diameter = 2 * radius

        # Create an invisible Entry widget in the middle of the screen
        entry_font = font.Font(family="Consolas", size=11)

        # Estimate the average character width using the font metrics
        average_char_width = entry_font.measure("0")

        # Calculate the entry width in characters based on the circle's diameter
        entry_width = (diameter - 20) // average_char_width

        self.entry = Entry(self.root, borderwidth=0, highlightthickness=0, bg="black", fg="white", justify="center", font=entry_font, width=entry_width, insertbackground="white")
        self.entry.place(x=center_x, y=center_y, anchor="center")

        # Set focus to the Entry widget to ensure the cursor is blinking
        self.entry.focus_set()

        def do_nothing(event):
            return 'break' # Do nothing when Backspace is pressed

        # Bind necessary events
        self.entry.bind('<space>', self.void_line)  # Bind Enter key to void_line method
        self.entry.bind('<Down>', self.on_key_press)  # Bind any key press to the on_key_press method
        self.entry.bind('<Control-z>', self.delete_except_highlighted)  # Bind Ctrl + Z to delete_except_highlighted method
        self.entry.bind('<Key>', self.hide_cursor)  # Bind any key press to hide the cursor
        self.entry.bind('<BackSpace>', do_nothing) # Bind Backspace to do nothing
        self.root.bind('<Motion>', self.show_cursor)  # Bind mouse motion to show the cursor

        self.canvas.configure(bg="black")

        self.current_line = None
        self.all_lines = []  # List to store all lines from all .txt files

        self.update_txt_files()  # Update txt_files based on current state

        # Start indexing lines in a separate thread
        self.indexing_thread = threading.Thread(target=self.index_all_lines)
        self.indexing_thread.start()

        # Set up file system watcher
        self.event_handler = FileSystemEventHandler()
        self.event_handler.on_modified = self.on_directory_change
        self.event_handler.on_created = self.on_directory_change
        self.event_handler.on_deleted = self.on_directory_change
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.void_dir, recursive=False)
        self.observer.start()

    def hide_cursor(self, event):
        self.entry.config(insertbackground="black")

    def show_cursor(self, event=None):
        self.entry.config(insertbackground="white")

    def update_txt_files(self):
        # Ensure the void directory exists
        if not os.path.exists(self.void_dir):
            os.makedirs(self.void_dir)

        # Ensure the 0.txt file exists
        if not os.path.exists(self.void_file_path):
            with open(self.void_file_path, 'w', encoding='utf-8') as void_file:
                void_file.write('')

        # Exclude '0.txt' when listing files
        self.txt_files = [f for f in os.listdir(self.void_dir) if f.endswith('.txt') and f != '0.txt']

    def index_all_lines(self):
        # Read and store all lines from all .txt files
        self.all_lines = []  # Reset list
        for txt_file in self.txt_files:
            file_path = os.path.join(self.void_dir, txt_file)
            if os.path.exists(file_path):  # Check if the file still exists
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    self.all_lines.extend([line.strip() for line in lines if line.strip()])

    def on_directory_change(self, event):
        # Update the file list and reindex lines on directory change
        self.update_txt_files()
        self.indexing_thread = threading.Thread(target=self.index_all_lines)
        self.indexing_thread.start()

    def on_key_press(self, event):
        if event.keysym == 'Down':
            self.show_random_line()
        self.hide_cursor(event)

    def show_random_line(self):
        if self.indexing_thread.is_alive():
            messagebox.showinfo("Indexing", "Please wait, indexing lines...")
            return

        # Filter out lines that contain only dots
        valid_lines = [line for line in self.all_lines if line.strip() != '.']

        if valid_lines:
            self.current_line = random.choice(valid_lines)
            self.entry.delete(0, tk.END)
            self.entry.insert(tk.END, self.current_line)
        else:
            self.update_txt_files()
            self.indexing_thread = threading.Thread(target=self.index_all_lines)
            self.indexing_thread.start()
            messagebox.showinfo("nothing found", "nothing found in the void")


    def void_line(self, event=None):
        line = self.entry.get().strip()
        if line:
            # Check if the line starts with "0"
            if line.startswith("0"):
                base, ext = os.path.splitext(self.void_file_path)
                if line == "0":
                    # Generate a random number with a random number of digits
                    num_digits = random.randint(1, 10)
                    random_number = ''.join([str(random.randint(0, 9)) for _ in range(num_digits)])
                    new_file_path = f"{base}_{random_number}{ext}"
                else:
                    # Use the rest of the line after "0" as the new name
                    new_name = line[1:]
                    new_file_path = os.path.join(self.void_dir, f"{new_name}{ext}")
                os.rename(self.void_file_path, new_file_path)
                # Create a new 0.txt file
                with open(self.void_file_path, 'w', encoding='utf-8') as void_file:
                    void_file.write('')
            else:
                # Regular input case (write the entered line)
                segments = [segment.strip() for segment in line.split('.') if segment.strip()]
                formatted_lines = []

                for segment in segments:
                    formatted_lines.append(segment + '\n')  # Add the segment
                    formatted_lines.append('.\n')           # Add a dot after each segment

                # Write each formatted line to the file
                if formatted_lines:  # Ensure there are valid lines to write
                    with open(self.void_file_path, 'a', encoding='utf-8') as void_file:
                        void_file.write(''.join(formatted_lines))
                        void_file.flush()
                        os.fsync(void_file.fileno())

        # Clear the entry field for the next input
        self.entry.delete(0, tk.END)
        self.entry.focus_set()
        self.show_cursor()  # Show the cursor again


    def delete_except_highlighted(self, event=None):
        try:
            selected_text = self.entry.selection_get()  # Get the highlighted text
            if selected_text:
                # Get the start and end indices of the selection
                start_index = self.entry.index(tk.SEL_FIRST)
                end_index = self.entry.index(tk.SEL_LAST)
                
                # Delete everything except the selected text
                self.entry.delete(0, tk.END)
                self.entry.insert(tk.END, selected_text)
                
                # Restore the selection
                self.entry.tag_add(tk.SEL, start_index, end_index)
            else:
                messagebox.showwarning("Warning", "No text is selected to keep.")
        except tk.TclError:
            messagebox.showwarning("Warning", "No text selected.")

# Main application entry point
if __name__ == "__main__":
    if getattr(sys, 'frozen', False):  # Check if running as a bundled exe
        app_path = os.path.dirname(sys.executable)
    else:
        app_path = os.path.dirname(__file__)

    void_dir = os.path.join(app_path, 'void')
    root = tk.Tk()
    app = VoiderInterface(root, void_dir)
    root.mainloop()