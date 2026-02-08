#!/usr/bin/env python3
import curses
import os
import time
import sys
import random
import glob
import argparse
from PIL import Image

# --- Configuration & Mode Setup ---
SMALL_RAMP = "@#S%?*+;:,. "
# noqa: W605 (This ignores the invalid escape sequence warning if not using a raw string)
BOURKE_RAMP = r"$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

def get_args():
    parser = argparse.ArgumentParser(description="ASCII Screen Art Screensaver")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", action="store_true", help="Use small character set and filter for 'a_' images")
    group.add_argument("-b", action="store_true", help="Use Paul Bourke ramp and filter for 'b_' images")
    return parser.parse_args()

# Cross-platform path detection
if sys.platform == "darwin":
    BASE_DIR = os.path.expanduser("~/Scripts/ScreenArt")
else:
    BASE_DIR = "/home/kenfasano/Scripts/ScreenArt"

IMG_DIR = os.path.join(BASE_DIR, "Images/TransformedImages")
INTERVAL = 10 

def scale_image(image, new_width):
    (original_width, original_height) = image.size
    aspect_ratio = original_height / float(original_width)
    # 0.5 multiplier accounts for terminal characters being taller than wide
    new_height = int(aspect_ratio * new_width * 0.5)
    return image.resize((new_width, new_height))

def get_ascii_frame(target_path, ascii_set, width):
    try:
        img = Image.open(target_path)
        img = scale_image(img, width)

        grayscale_img = img.convert("L")
        rgb_img = img.convert("RGB")

        pixels_gray = grayscale_img.load()
        pixels_rgb = rgb_img.load()

        scale_factor = 255 / (len(ascii_set) - 1)
        lines = []
        for y in range(img.height):
            line_parts = []
            for x in range(img.width):
                r, g, b = pixels_rgb[x, y] #type: ignore
                brightness = pixels_gray[x, y] # type: ignore

                char_idx = int(brightness / scale_factor) #type: ignore
                char_idx = min(char_idx, len(ascii_set) - 1)

                char = ascii_set[char_idx]
                # TrueColor ANSI escape sequence
                line_parts.append(f"\x1b[38;2;{r};{g};{b}m{char}")
            lines.append("".join(line_parts) + "\x1b[0m")
        return lines
    except Exception as e:
        return [f"Error loading {target_path}: {e}"]

def run_screensaver(stdscr, args):
    """
    stdscr is provided by curses.wrapper. 
    We use it to hide the cursor and listen for 'q', 
    but use sys.stdout for RGB printing.
    """
    # 1. Hide the cursor reliably across Ghostty/Wayland/macOS
    curses.curs_set(0) 
    stdscr.nodelay(True) # Non-blocking input check
    
    selected_ramp = BOURKE_RAMP if args.b else SMALL_RAMP
    prefix = "b_" if args.b else "a_"
    extensions = ('*.jpg', '*.jpeg', '*.png', '*.bmp')
    # Aggressive hide: Clear and send DECTCEM hide sequence
    sys.stdout.write("\x1b[2J\x1b[?25l")
    sys.stdout.flush()

    # Initial clear
    sys.stdout.write("\x1b[2J")

    try:
        while True:
            # Check if 'q' was pressed
            if stdscr.getch() == ord('q'):
                break

            # Find images
            image_list = []
            for ext in extensions:
                image_list.extend(glob.glob(os.path.join(IMG_DIR, ext)))
            
            if not image_list:
                print(f"No images found in {IMG_DIR}")
                break

            filtered_list = [img for img in image_list if os.path.basename(img).startswith(prefix)]
            target_path = random.choice(filtered_list if filtered_list else image_list)

            # Get dynamic width in case window resized
            width = os.get_terminal_size().columns - 2
            new_frame = get_ascii_frame(target_path, selected_ramp, width)

            # Render: Move cursor to top-left and print
            # The "Nuclear" Cursor Hide:
            # We move to home \x1b[H and RE-HIDE the cursor \x1b[?25l on every single frame
            output = "\x1b[H\x1b[?25l" + "\n".join(new_frame)
            sys.stdout.write(output)
            sys.stdout.flush()
            sys.stdout.write(output)
            sys.stdout.flush()
            
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    args = get_args()
    # wrapper ensures cursor is restored even if the script crashes
    curses.wrapper(run_screensaver, args)
