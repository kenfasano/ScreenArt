#!/usr/bin/env python3
import os
import time
import datetime
import sys
import random
import glob
import argparse
from PIL import Image

# --- Configuration & Mode Setup ---
SMALL_RAMP = "@#S%?*+;:,. "
BOURKE_RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

def get_args():
    parser = argparse.ArgumentParser(description="ASCII Screen Art Screensaver")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", action="store_true", help="Use small character set and filter for 'a_' images")
    group.add_argument("-b", action="store_true", help="Use Paul Bourke ramp and filter for 'b_' images")
    return parser.parse_args()

# Cross-platform path detection
if sys.platform == "darwin":
    BASE_DIR = "/Volumes/Shared/Scripts/ScreenArt"
else:
    BASE_DIR = "/home/kenfasano/Scripts/ScreenArt"

IMG_DIR = os.path.join(BASE_DIR, "Images/TransformedImages")
LOG_FILE = os.path.join(BASE_DIR, "asciiScreenArt.log")
WIDTH = os.get_terminal_size().columns - 2
INTERVAL = 10 

def log_message(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

def scale_image(image, new_width):
    (original_width, original_height) = image.size
    aspect_ratio = original_height / float(original_width)
    new_height = int(aspect_ratio * new_width * 0.5)
    return image.resize((new_width, new_height))

def get_ascii_frame(target_path, ascii_set):
    try:
        img = Image.open(target_path)
        img = scale_image(img, WIDTH)

        grayscale_img = img.convert("L")
        rgb_img = img.convert("RGB")

        # Fast PixelAccess (no len() error)
        pixels_gray = grayscale_img.load()
        pixels_rgb = rgb_img.load()

        scale_factor = 255 / (len(ascii_set) - 1)
        lines = []
        for y in range(img.height):
            line_parts = []
            for x in range(img.width):
                r, g, b = pixels_rgb[x, y] # type: ignore
                brightness = pixels_gray[x, y] # type: ignore

                char_idx = int(brightness / scale_factor) # type: ignore
                if char_idx >= len(ascii_set):
                    char_idx = len(ascii_set) - 1

                char = ascii_set[char_idx]
                line_parts.append(f"\x1b[38;2;{r};{g};{b}m{char}\x1b[0m")
            lines.append("".join(line_parts))
        return lines
    except Exception as e:
        return [f"Error loading {target_path}: {e}"]

def transition_wipe(new_frame, delay=0.01):
    for i, line in enumerate(new_frame):
        sys.stdout.write(f"\x1b[{i+1};1H{line}")
        sys.stdout.flush()
        time.sleep(delay)

def run_screensaver(args):
    # Determine mode settings
    selected_ramp = BOURKE_RAMP if args.b else SMALL_RAMP
    prefix = "b_" if args.b else "a_"

    sys.stdout.write("\x1b[?25l") # Hide cursor
    os.system('clear')

    extensions = ('*.jpg', '*.jpeg', '*.png', '*.bmp')

    try:
        while True:
            # 1. Gather and filter images immediately
            image_list = []
            for ext in extensions:
                image_list.extend(glob.glob(os.path.join(IMG_DIR, ext)))

            # 2. Selection loop for A/B grades
            filtered_list = [img for img in image_list if os.path.basename(img).startswith(prefix)]
            
            if not filtered_list:
                if not image_list:
                    log_message(f"No images found in {IMG_DIR}")
                    time.sleep(5)
                target_path = random.choice(image_list)
            else:
                target_path = random.choice(filtered_list)

            # 3. Log, Generate and Display
            log_message(f"Displaying ({prefix}): {os.path.basename(target_path)}")
            new_frame = get_ascii_frame(target_path, selected_ramp)

            # 4. Simple Wipe Transition
            transition_wipe(new_frame)
            
            # 5. Wait for the set interval before next image
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        sys.stdout.write("\x1b[?25h")
        os.system('clear')
        print("Stopped by user.")
    except Exception as e:
        sys.stdout.write("\x1b[?25h")
        print(f"fatal error: {e}")
        
if __name__ == "__main__":
    args = get_args()
    run_screensaver(args)
