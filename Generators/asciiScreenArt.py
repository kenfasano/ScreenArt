import glob
import os
import random
from PIL import Image, ImageDraw, ImageFont

from .text import Text

SMALL_RAMP  = "@#S%?*+;:,. "
BOURKE_RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "


class AsciiScreenArt(Text):
    RAMPS = [SMALL_RAMP, BOURKE_RAMP]

    def __init__(self, out_dir: str):
        super().__init__(out_dir)
        self.file_count = self.config.get("file_counts", {}).get("ascii_screen_art", 5)
        self._src_dir = os.path.expanduser(
            self.config.get("paths", {}).get("transformers_out", "")
        )
        self._char_size: int = self.config.get("ascii_screen_art", {}).get("char_size", 10)
        self._setup_mono_font()

    def _setup_mono_font(self) -> None:
        if self.os_type == "darwin":
            self._mono_font_path = "/System/Library/Fonts/Menlo.ttc"
        else:
            self._mono_font_path = "/usr/share/fonts/liberation-mono-fonts/LiberationMono-Regular.ttf"

    def _get_ascii_grid(self, src: Image.Image, ramp: str,
                        cols: int, rows: int) -> list[list[tuple[str, int, int, int]]]:
        """Downscale src to (cols, rows) and map each pixel to (char, r, g, b)."""
        img  = src.resize((cols, rows), Image.LANCZOS)
        gray = img.convert("L")
        rgb  = img.convert("RGB")

        gray_px = gray.load()
        rgb_px  = rgb.load()
        scale   = 255.0 / (len(ramp) - 1)

        grid: list[list[tuple[str, int, int, int]]] = []
        for y in range(rows):
            row: list[tuple[str, int, int, int]] = []
            for x in range(cols):
                brightness = gray_px[x, y]   # type: ignore[index]
                r, g, b    = rgb_px[x, y]    # type: ignore[index]
                idx        = min(int(brightness / scale), len(ramp) - 1)
                row.append((ramp[idx], r, g, b))
            grid.append(row)
        return grid

    def _render_ascii_image(self, src_path: str, ramp: str) -> Image.Image | None:
        try:
            src = Image.open(src_path).convert("RGB")
        except Exception as e:
            self.log.debug(f"Failed to open {src_path}: {e}")
            return None

        try:
            font = ImageFont.truetype(self._mono_font_path, self._char_size)
        except Exception:
            font = ImageFont.load_default()

        # Measure a single character cell
        dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        bbox   = dummy.textbbox((0, 0), "A", font=font)
        cell_w = max(bbox[2] - bbox[0], 1)
        cell_h = max(bbox[3] - bbox[1], 1)

        cols = self.width  // cell_w
        rows = self.height // cell_h

        grid   = self._get_ascii_grid(src, ramp, cols, rows)
        canvas = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        draw   = ImageDraw.Draw(canvas)

        for y, row in enumerate(grid):
            for x, (char, r, g, b) in enumerate(row):
                draw.text((x * cell_w, y * cell_h), char, fill=(r, g, b), font=font)

        return canvas

    def run(self) -> None:
        if not self._src_dir or not os.path.isdir(self._src_dir):
            self.log.debug(f"Source dir not found: {self._src_dir}")
            return

        image_list: list[str] = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
            image_list.extend(glob.glob(os.path.join(self._src_dir, ext)))

        if not image_list:
            self.log.debug("No source images found for AsciiScreenArt")
            return

        for i in range(self.file_count):
            src_path = random.choice(image_list)
            ramp     = random.choice(self.RAMPS)
            img      = self._render_ascii_image(src_path, ramp)
            if img is None:
                self.log.debug(f"Failed to render ASCII art from {src_path}")
                continue

            out_path = os.path.join(self.out_dir, f"ascii_{i}.jpeg")
            try:
                img.save(out_path, quality=95)
                self.log.debug(f"Saved: {out_path}")
            except Exception as e:
                self.log.debug(f"Failed to save {out_path}: {e}")
