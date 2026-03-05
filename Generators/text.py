# ── module-level ──────────────────────────────────────────────────────────────
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont, ImageFont as BitmapFont
import os
import json
import hashlib
from functools import lru_cache
from .drawGenerator import DrawGenerator

_FONT_CACHE_PATH = os.path.join(os.path.dirname(__file__), "_font_size_cache.json")
_font_size_cache: dict[str, int] = {}
_dummy_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))


def _make_cache_key(font_path: str, lines: tuple[str, ...],
                    usable_width: int, usable_height: int) -> str:
    lines_hash = hashlib.md5("||".join(lines).encode("utf-8")).hexdigest()
    return f"{font_path}|{lines_hash}|{usable_width}|{usable_height}"


def _load_font_size_cache() -> None:
    global _font_size_cache
    try:
        with open(_FONT_CACHE_PATH, 'r') as f:
            _font_size_cache = json.load(f)
    except FileNotFoundError:
        _font_size_cache = {}

def _save_font_size_cache() -> None:
    with open(_FONT_CACHE_PATH, 'w') as f:
        json.dump(_font_size_cache, f)


@lru_cache(maxsize=256)
def _load_font_cached(font_path: str, size: int) -> FreeTypeFont | BitmapFont:
    try:
        return ImageFont.truetype(font_path, size)
    except IOError:
        return ImageFont.load_default()


def _warm_font_cache() -> None:
    """Pre-load every (font_path, size) pair from the persisted cache into lru_cache."""
    seen: set[tuple[str, int]] = set()
    for key, size in _font_size_cache.items():
        font_path = key.split("|")[0]
        pair = (font_path, size)
        if pair not in seen:
            seen.add(pair)
            _load_font_cached(font_path, size)  # warms lru_cache


def _find_max_font_size_cached(font_path: str, lines: tuple[str, ...],
                                usable_width: int, usable_height: int) -> int:
    key = _make_cache_key(font_path, lines, usable_width, usable_height)
    if key in _font_size_cache:
        return _font_size_cache[key]

    estimated_max = min(500, usable_height // max(len(lines), 1))
    low, high, best = 1, estimated_max, 0
    while low <= high:
        mid = (low + high) // 2
        font = _load_font_cached(font_path, mid)
        max_width, total_height = 0, 0
        for line in lines:
            bbox = _dummy_draw.textbbox((0, 0), line, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            max_width = max(max_width, w)
            total_height += h + (h // 2)
        if max_width <= usable_width and total_height <= usable_height:
            best = mid
            low = mid + 1
        else:
            high = mid - 1

    _font_size_cache[key] = best
    _save_font_size_cache()
    return best


# ── Run once at import time ────────────────────────────────────────────────────
_load_font_size_cache()
_warm_font_cache()


# ── class ─────────────────────────────────────────────────────────────────────
class Text(DrawGenerator):
    """
    Utility Generator for drawing text on images.
    Provides canvas creation, dynamic font scaling, and text wrapping.
    """

    def __init__(self):
        super().__init__()
        self.width = self.config.get("canvas_width", 1920)
        self.height = self.config.get("canvas_height", 1080)
        self.border_size = self.config.get("border_size", 15)
        self.min_font_size = self.config.get("min_font_size", 20)
        self.usable_width = self.width - (2 * self.border_size)
        self.usable_height = self.height - (2 * self.border_size)
        self._setup_fonts()

    def _setup_fonts(self) -> None:
        """Maps font paths based on the current operating system."""
        if self.os_type == "darwin":
            self.language_fonts = {
                "Tibetan": os.path.expanduser("~/Library/Fonts/NotoSerifTibetan-VariableFont_wght.ttf"),
                "Hebrew":  "/System/Library/Fonts/ArialHB.ttc",
                "English": "/System/Library/Fonts/Supplemental/Arial.ttf",
            }
        else:
            self.language_fonts = {
                "Tibetan": "/usr/share/fonts/jomolhari-fonts/Jomolhari-alpha3c-0605331.ttf",
                "Hebrew":  "/usr/share/fonts/google-noto-vf/NotoSansHebrew[wght].ttf",
                "English": "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
            }

    def _load_font(self, font_path: str, size: int) -> FreeTypeFont | BitmapFont:
        return _load_font_cached(font_path, size)

    def _find_max_font_size(self, font_path: str, lines: list[str]) -> int:
        return _find_max_font_size_cached(
            font_path, tuple(lines), self.usable_width, self.usable_height
        )

    def get_max_font_size(self, font_path: str, lines: list[str]) -> tuple[int, list[str]]:
        """
        Find the largest font size that fits the text.
        Falls back to the second half of the text if the full block renders too small.
        """
        if not lines:
            self.log.debug("No text lines provided to font scaler.")
            return 10, ["Error: No text loaded."]

        size = self._find_max_font_size(font_path, lines)
        if size >= self.min_font_size:
            return size, lines

        # Full text too dense — try the second half
        half = lines[len(lines) // 2:]
        half_size = self._find_max_font_size(font_path, half)
        if half_size >= self.min_font_size:
            return half_size, half

        return size, lines  # best effort with full text

    def generate_text_image(self,
                            lines_to_draw: list[str],
                            language: str = "English",
                            bg_color: str = "black",
                            fg_color: str = "white") -> Image.Image:
        """Create a canvas, fit the font, draw the text, and return the image."""
        font_path = self.language_fonts.get(language, self.language_fonts["English"])
        font_size, lines_to_draw = self.get_max_font_size(font_path, lines_to_draw)
        font = _load_font_cached(font_path, font_size)

        img = Image.new('RGB', (self.width, self.height), bg_color)
        drawing = ImageDraw.Draw(img)
        y = self.border_size

        for i, line in enumerate(lines_to_draw):
            bbox = drawing.textbbox((0, 0), str(line), font=font)
            h = bbox[3] - bbox[1]
            drawing.text((self.border_size + 10, y), line, fill=fg_color, font=font)
            y += h + (h // 2)   # 1.5× line spacing
            if i == 0:
                y += 15          # extra gap after title line
            if y >= self.height - 50:
                self.log.debug(f"Text exceeded canvas height at line {i}")
                break

        return img
