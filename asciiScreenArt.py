#!/usr/bin/env python3
import os
import time
import sys
import random
import glob
import argparse
import signal
from PIL import Image

# ================= Configuration =================

SMALL_RAMP = "@#S%?*+;:,. "
BOURKE_RAMP = r"$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

INTERVAL = 10          # seconds between images
TARGET_FPS = 30        # adaptive upper bound
FADE_DURATION = 0.5    # seconds

# ================= Terminal Control =================

def enter_alt_screen():
    sys.stdout.write("\033[?1049h\033[H\033[?25l")
    sys.stdout.write("\033[?7l")  # disable wrap
    sys.stdout.flush()

def exit_alt_screen():
    sys.stdout.write("\033[?1049l\033[?25h\033[0m")
    sys.stdout.write("\033[?7h")  # restore wrap
    sys.stdout.flush()

def detect_terminal():
    term = os.environ.get("TERM", "")
    colorterm = os.environ.get("COLORTERM", "")

    truecolor = (
        "truecolor" in colorterm.lower()
        or "24bit" in colorterm.lower()
        or term.endswith("-direct")
    )

    return {
        "truecolor": truecolor,
        "macos": sys.platform == "darwin",
        "linux": sys.platform.startswith("linux"),
    }

# ================= Image Processing =================

def build_ascii_frame(path, ramp, width):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    height = max(1, int((h / w) * width * 0.5))
    img = img.resize((width, height))

    pixels = img.load()
    scale = 255 / (len(ramp) - 1)
    frame = []

    for y in range(img.height):
        row = []
        for x in range(img.width):
            r, g, b = pixels[x, y]
            lum = int(0.299*r + 0.587*g + 0.114*b)
            idx = min(int(lum / scale), len(ramp) - 1)
            row.append(((r, g, b), idx))
        frame.append(row)

    return frame

# ================= Rendering =================

def render_frame(frame, ramp, caps):
    lines = []
    for y, row in enumerate(frame):
        s = []
        for (r, g, b), idx in row:
            ch = ramp[idx]
            if caps["truecolor"]:
                s.append(f"\033[38;2;{r};{g};{b}m{ch}")
            else:
                s.append(ch)
        lines.append(f"\033[?25l\033[{y+1};1H" + "".join(s) + "\033[0m")

    return "".join(lines)

def render_fade(old, new, ramp, alpha, caps):
    lines = []
    max_y = min(len(old), len(new))

    for y in range(max_y):
        s = []
        for p1, p2 in zip(old[y], new[y]):
            (r1, g1, b1), i1 = p1
            (r2, g2, b2), i2 = p2

            r = int(r1 * (1 - alpha) + r2 * alpha)
            g = int(g1 * (1 - alpha) + g2 * alpha)
            b = int(b1 * (1 - alpha) + b2 * alpha)
            idx = int(i1 * (1 - alpha) + i2 * alpha)

            ch = ramp[idx]
            if caps["truecolor"]:
                s.append(f"\033[38;2;{r};{g};{b}m{ch}")
            else:
                s.append(ch)

        lines.append(f"\033[{y+1};1H" + "".join(s) + "\033[0m")

    return "".join(lines)

# ================= Main =================

def main():
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group()
    g.add_argument("-a", action="store_true", help="Small ramp")
    g.add_argument("-b", action="store_true", help="Bourke ramp")
    args = parser.parse_args()

    ramp = BOURKE_RAMP if args.b else SMALL_RAMP

    base = os.path.expanduser("~/Scripts/ScreenArt") \
        if sys.platform == "darwin" else "/home/kenfasano/Scripts/ScreenArt"
    img_dir = os.path.join(base, "Images/TransformedImages")

    images = []
    for ext in ("*.jpg", "*.png", "*.jpeg", "*.bmp", "*.webp"):
        images += glob.glob(os.path.join(img_dir, ext))

    if not images:
        print("No images found")
        return

    caps = detect_terminal()

    # ---- terminal state ----
    resized = True
    try:
        sz = os.get_terminal_size()
        term_width, term_height = sz.columns, sz.lines
    except OSError:
        term_width, term_height = 80, 24

    def handle_winch(signum, frame):
        nonlocal resized, term_width, term_height
        try:
            sz = os.get_terminal_size()
            term_width, term_height = sz.columns, sz.lines
        except OSError:
            pass
        resized = True

    signal.signal(signal.SIGWINCH, handle_winch)

    enter_alt_screen()

    current = None
    last_switch = 0.0
    target_frame_time = 1.0 / TARGET_FPS

    try:
        while True:
            now = time.time()

            # Pick new image if needed
            if resized or current is None or now - last_switch >= INTERVAL:
                next_frame = build_ascii_frame(
                    random.choice(images), ramp, term_width
                )
                resized = False

                if current:
                    steps = max(1, int(FADE_DURATION * TARGET_FPS))
                    for i in range(steps + 1):
                        t0 = time.time()
                        alpha = i / steps
                        buf = render_fade(current, next_frame, ramp, alpha, caps)
                        sys.stdout.write(buf)
                        sys.stdout.flush()

                        # ---- adaptive FPS ----
                        elapsed = time.time() - t0
                        sleep = target_frame_time - elapsed
                        if sleep > 0:
                            time.sleep(sleep)
                else:
                    buf = render_frame(next_frame, ramp, caps)
                    sys.stdout.write(buf)
                    sys.stdout.flush()

                current = next_frame
                last_switch = time.time()

            else:
                # Idle redraw throttling (adaptive DPS)
                time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        exit_alt_screen()

# ================= Entry =================

if __name__ == "__main__":
    main()

