#!/usr/bin/env python3
"""Minimal ScreenArt Video Maker GUI
Dependencies: pip install pillow numpy opencv-python
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import logging
import math
import queue
import threading
import os
import tempfile
from PIL import Image, ImageTk
import numpy as np
import cv2
import sys
from pathlib import Path

# Add project root and Transformers dir to sys.path
ROOT_DIR = Path(__file__).resolve().parent
TRANSFORMERS_DIR = ROOT_DIR / "Transformers"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(TRANSFORMERS_DIR))

# Logging -> queue -> UI sink
log_queue = queue.Queue()

class QueueHandler(logging.Handler):
    def emit(self, record):
        log_queue.put(self.format(record))

logger = logging.getLogger("video_maker")
logger.setLevel(logging.INFO)
qh = QueueHandler()
qh.setFormatter(logging.Formatter("%(asctime)s - %(message)s", "%H:%M:%S"))
logger.addHandler(qh)

# ---------------------------
# Basic warp transform (fast-ish)
# ---------------------------
def horizontal_sine_warp(pil_img: Image.Image, intensity: float = 0.0) -> Image.Image:
    """
    Apply a horizontal sinusoidal warp to the entire image.
    intensity: 0.0 (no warp) -> 1.0 (strong)
    """
    if intensity == 0.0:
        return pil_img.copy()

    arr = np.array(pil_img)
    h, w = arr.shape[:2]
    result = np.zeros_like(arr)

    # amplitude scales with intensity and width
    amp = intensity * max(1, w * 0.02)
    freq = 2 * np.pi / max(1, h * 0.2)  # vertical wavelength

    # Use vectorized mapping for speed
    ys = np.arange(h)
    offsets = (amp * np.sin(freq * ys)).astype(np.int32)  # offset per row

    for y in range(h):
        off = offsets[y]
        if off > 0:
            result[y, off:] = arr[y, :-off]
            result[y, :off] = arr[y, -off:]
        elif off < 0:
            o = -off
            result[y, :-o] = arr[y, o:]
            result[y, -o:] = arr[y, :o]
        else:
            result[y] = arr[y]

    return Image.fromarray(result)

def radial_ripple_warp(image: Image.Image, amplitude: float = 10.0, wavelength: float = 30.0) -> Image.Image:
    """Apply a radial ripple distortion to the image."""
    width, height = image.size
    cx, cy = width / 2.0, height / 2.0

    src_pixels = image.load()
    warped = Image.new("RGB", (width, height))
    dst_pixels = warped.load()

    for y in range(height):
        for x in range(width):
            # Distance from center
            dx = x - cx
            dy = y - cy
            r = math.hypot(dx, dy)

            # Calculate ripple offset
            ripple = amplitude * math.sin(r / wavelength * 2 * math.pi)

            # Move pixel inward or outward along radial direction
            if r != 0:
                nx = int(cx + dx * (1 + ripple / r))
                ny = int(cy + dy * (1 + ripple / r))
            else:
                nx, ny = x, y

            # Boundary check
            if 0 <= nx < width and 0 <= ny < height:
                dst_pixels[x, y] = src_pixels[nx, ny]
            else:
                dst_pixels[x, y] = (0, 0, 0)  # black background for out-of-bounds

    return warped
# ---------------------------
# ---------------------------
# Video production functions
# ---------------------------
def make_forward_segment(image_path, tmp_segment_path, duration_secs=5.0, fps=30, start_intensity=0.5, end_intensity=0.51, logger=logger):
    """
    Produce a forward segment mp4 at tmp_segment_path by evolving warp intensity linearly.
    """
    logger.info(f"Generating forward segment to {tmp_segment_path}")
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(tmp_segment_path, fourcc, fps, (w, h))

    total_frames = int(max(1, round(duration_secs * fps)))
    start_amplitude = 0.1
    end_amplitude = 20.0
    start_wavelength = 0.1
    end_wavelength = 60.0

    for i in range(total_frames):
        t = i / (total_frames - 1) if total_frames > 1 else 0.0
        amplitude = (1 - t) * start_amplitude + t * end_amplitude
        wavelength = (1 - t) * start_wavelength + t * end_wavelength
        warped = radial_ripple_warp(img, amplitude, wavelength)
        frame = cv2.cvtColor(np.array(warped), cv2.COLOR_RGB2BGR)
        writer.write(frame)
        if i % max(1, total_frames // 50) == 0:
            logger.info(f"Forward: frame {i+1}/{total_frames}")
    writer.release()
    logger.info("Forward segment complete")
    return total_frames, (w, h), fps

def append_reverse_with_crossfade(tmp_segment_path, output_path, fade_seconds=1.0, logger=logger):
    """
    Stream the tmp_segment_path forward, then append its reversed frames with a crossfade,
    writing to output_path. Does not load all frames at once (seeks).
    """
    logger.info(f"Appending reversed segment with crossfade into {output_path}")
    cap = cv2.VideoCapture(tmp_segment_path)
    if not cap.isOpened():
        raise RuntimeError("Could not open temporary segment for reading")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info(f"Segment properties: fps={fps}, frames={frame_count}, size={width}x{height}")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # 1) write forward frames (stream)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    written = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        written += 1
        if written % max(1, frame_count // 50) == 0:
            logger.info(f"Writing forward frames: {written}/{frame_count}")

    # 2) crossfade (fade_seconds)
    fade_frames = int(max(1, round(fps * fade_seconds)))
    cap2 = cv2.VideoCapture(tmp_segment_path)
    for i in range(fade_frames):
        alpha = 1.0 - (i / fade_frames)
        forward_index = frame_count - fade_frames + i
        reverse_index = frame_count - 1 - i

        cap.set(cv2.CAP_PROP_POS_FRAMES, forward_index)
        ret_fwd, frame_fwd = cap.read()
        cap2.set(cv2.CAP_PROP_POS_FRAMES, reverse_index)
        ret_rev, frame_rev = cap2.read()
        if not (ret_fwd and ret_rev):
            continue
        blended = cv2.addWeighted(frame_fwd, alpha, frame_rev, 1.0 - alpha, 0)
        out.write(blended)
    logger.info("Crossfade forward->reverse written")

    # 3) remaining reversed frames
    for i in range(frame_count - fade_frames - 1, -1, -1):
        cap2.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap2.read()
        if not ret:
            continue
        out.write(frame)
        if (frame_count - i) % max(1, frame_count // 50) == 0:
            logger.info(f"Writing reversed frames: {frame_count - i}/{frame_count}")

    # 4) crossfade reverse->start to make seamless loop
    cap3 = cv2.VideoCapture(tmp_segment_path)
    for i in range(fade_frames):
        alpha = 1.0 - (i / fade_frames)
        rev_idx = i  # beginning of reversed sequence (near end of overall output)
        fwd_idx = i  # beginning of original forward
        cap2.set(cv2.CAP_PROP_POS_FRAMES, rev_idx)
        ret_rev, frame_rev = cap2.read()
        cap3.set(cv2.CAP_PROP_POS_FRAMES, fwd_idx)
        ret_fwd, frame_fwd = cap3.read()
        if not (ret_rev and ret_fwd):
            continue
        blended = cv2.addWeighted(frame_rev, alpha, frame_fwd, 1.0 - alpha, 0)
        out.write(blended)
    logger.info("Crossfade reverse->start written (loop seam)")

    cap.release()
    cap2.release()
    cap3.release()
    out.release()
    logger.info("Final video written")

class VideoMakerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ScreenArt Video Maker")
        self.geometry("1000x700")
        self.minsize(800, 600)

        self.selected_image = None
        self.image_path = None
        self.output_path = None

        self._build_ui()
        self._poll_log_queue()

    def _build_ui(self):
        # Top frame: controls
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        btn_select = ttk.Button(top, text="Select Image", command=self.select_image)
        btn_select.pack(side=tk.LEFT)

        self.label_image = ttk.Label(top, text="No image selected", width=60)
        self.label_image.pack(side=tk.LEFT, padx=8)

        btn_save = ttk.Button(top, text="Choose Save File", command=self.choose_save)
        btn_save.pack(side=tk.LEFT, padx=(8,0))

        self.btn_create = ttk.Button(top, text="Create Video", command=self.create_video_thread)
        self.btn_create.pack(side=tk.RIGHT)

        # Middle: preview area (most of window)
        preview_frame = ttk.Frame(self)
        preview_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=6)

        self.canvas = tk.Canvas(preview_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bottom: progress and log
        bottom = ttk.Frame(self, relief=tk.GROOVE)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=6)

        progress_label = ttk.Label(bottom, text="Progress:")
        progress_label.pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(bottom, length=300, mode="determinate")
        self.progress.pack(side=tk.LEFT, padx=8)

        self.status_var = tk.StringVar(value="Idle")
        status_label = ttk.Label(bottom, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=8)

        # Scrolled log area
        self.logbox = scrolledtext.ScrolledText(bottom, height=6, state="disabled")
        self.logbox.pack(side=tk.BOTTOM, fill=tk.X, pady=(6,0))

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files","*.*")])
        if not path:
            return
        self.label_image.config(text=path)
        logger.info(f"Selected image: {path}")


    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files","*.*")])
        if not path:
            return
        self.image_path = path
        self._load_preview(path)
        logger.info(f"Selected image: {path}")

    def _load_preview(self, path):
        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            return
        # scale to canvas while preserving aspect
        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 450
        iw, ih = img.size
        scale = min(cw/iw, ch/ih, 1.0)
        nw, nh = int(iw*scale), int(ih*scale)
        img_tk = ImageTk.PhotoImage(img.resize((nw, nh), Image.LANCZOS))
        self.canvas.image = img_tk  # keep ref
        self.canvas.delete("all")
        self.canvas.create_image((cw//2, ch//2), image=img_tk, anchor="center")
        self.label_image.config(text=os.path.basename(path))

    def choose_save(self):
        path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 video","*.mp4")])
        if not path:
            return
        self.output_path = path
        logger.info(f"Output will be: {path}")

    def create_video_thread(self):
        if not self.image_path:
            messagebox.showwarning("No image", "Please select an input image first.")
            return
        if not self.output_path:
            messagebox.showwarning("No output", "Please choose a save file for the output video.")
            return

        # Disable Create button while running
        self.btn_create.config(state="disabled")
        self.progress["value"] = 0
        self.status_var.set("Starting...")

        thr = threading.Thread(target=self._create_video, daemon=True)
        thr.start()

    def _create_video(self):
        try:
            # Use a temp file for the forward segment
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
            os.close(tmp_fd)
            try:
                # Produce forward segment
                duration = 5.0   # seconds (tunable)
                fps = 30
                start_intensity = 0.00
                end_intensity = 1.00
                total_frames, (w,h), used_fps = make_forward_segment(
                    self.image_path, tmp_path,
                    duration_secs=duration, fps=fps,
                    start_intensity=start_intensity, end_intensity=end_intensity,
                    logger=logger
                )
                # Update progress to 40% (arbitrary split)
                self._set_progress(40, f"Forward frames complete: {total_frames}")

                # Now stream append reversed + crossfade into final output
                append_reverse_with_crossfade(tmp_path, self.output_path, fade_seconds=1.0, logger=logger)

                self._set_progress(100, f"Video saved: {self.output_path}")
                messagebox.showinfo("Done", f"Video created:\n{self.output_path}")
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        except Exception as e:
            logger.exception("Error while creating video")
            messagebox.showerror("Error", f"Video creation failed:\n{e}")
        finally:
            self.btn_create.config(state="normal")
            self.status_var.set("Idle")

    def _set_progress(self, value, status_text=None):
        # run in UI thread
        def _ui():
            self.progress["value"] = value
            if status_text:
                self.status_var.set(status_text)
        self.after(1, _ui)

    def _poll_log_queue(self):
        # Periodically copy log_queue into logbox
        try:
            while True:
                msg = log_queue.get_nowait()
                self.logbox.config(state="normal")
                self.logbox.insert(tk.END, msg + "\n")
                self.logbox.see(tk.END)
                self.logbox.config(state="disabled")
                # update a small progress-like status from logs
                if "Forward: frame" in msg:
                    # crude heuristic to set progress between 0 and 40
                    try:
                        part = msg.split("Forward: frame")[1].strip().split("/")[0]
                        idx = int(part)
                        # update percentage
                        self.progress["value"] = min(40, (idx / 1.0) + self.progress["value"]*0)  # keep simple
                    except Exception:
                        pass
        except queue.Empty:
            pass
        finally:
            self.after(200, self._poll_log_queue)

if __name__ == "__main__":
    app = VideoMakerApp()
    app.mainloop()
if __name__ == "__main__":
    app = VideoMakerApp()
    app.mainloop()
