#!/usr/bin/env python3

import os
import sys
import time
import logging
try:
    from PIL import Image
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import scrolledtext

# Set up logging
default_log = os.path.join(os.path.dirname(__file__), "ascii_art_gui.log")
logging.basicConfig(
    filename=default_log,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

ASCII_CHARS = "@%#*+=-:. "

def resize_image(image, new_width=100):
    width, height = image.size
    aspect_ratio = height / width
    new_height = int(aspect_ratio * new_width * 0.55)  # adjust for font aspect ratio
    return image.resize((new_width, new_height))

def grayify(image):
    return image.convert("L")

def pixels_to_ascii(image):
    pixels = image.getdata()
    chars = "".join([ASCII_CHARS[pixel * len(ASCII_CHARS) // 256] for pixel in pixels])
    return chars

def convert_to_ascii(path):
    image = Image.open(path)
    # Resize if too wide
    if image.width > 100:
        image = resize_image(image, new_width=100)
    gray_image = grayify(image)
    ascii_str = pixels_to_ascii(gray_image)
    width = gray_image.width
    # Split string into lines
    ascii_img = "\n".join(
        [ascii_str[i:(i + width)] for i in range(0, len(ascii_str), width)]
    )
    return ascii_img

def browse_and_convert():
    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All Files", "*.*")]
    )
    if not file_path:
        return
    logging.info(f"Selected file: {file_path}")
    start_time = time.time()
    try:
        ascii_art = convert_to_ascii(file_path)
        duration = time.time() - start_time
        logging.info(f"Processing time: {duration:.2f}s")
        logging.info("ASCII Art output:\n" + ascii_art)
        show_ascii_art(ascii_art)
    except Exception as e:
        logging.error(f"Error during conversion: {e}", exc_info=True)
        messagebox.showerror("Error", f"Failed to convert image:\n{e}")

def show_ascii_art(ascii_art):
    win = tk.Toplevel(root)
    win.title("ASCII Art")
    txt = scrolledtext.ScrolledText(win, wrap=tk.NONE, width=100, height=40)
    txt.insert(tk.END, ascii_art)
    txt.configure(state='disabled')
    txt.pack(fill=tk.BOTH, expand=True)

# Main application window
root = tk.Tk()
root.title("ASCII Art Converter")

btn = tk.Button(root, text="Browse", command=browse_and_convert)
btn.pack(pady=20)

root.mainloop()
