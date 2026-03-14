# ── module-level ──────────────────────────────────────────────────────────────
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont, ImageFont as BitmapFont
import os
import json
import hashlib
import random
import atexit
from functools import lru_cache
from .drawGenerator import DrawGenerator

_FONT_CACHE_PATH = os.path.join(os.path.dirname(__file__), "_font_size_cache.json")
_font_size_cache: dict[str, int] = {}
_font_cache_dirty: bool = False
_dummy_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))

# Layout modes with weights
_LAYOUT_MODES = [
    ("tile",    1.0),
    ("hero",    1.0),
    ("scatter", 1.0),
    ("columns", 1.0),
]


def _complement_rgb(r: int, g: int, b: int) -> tuple[int, int, int]:
    """Return the HSV hue-complement (hue +180°) of an RGB color."""
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    h2 = (h + 0.5) % 1.0
    # Boost saturation and value so complement is never washed out
    s2 = max(s, 0.5)
    v2 = max(v, 0.45)
    cr, cg, cb = colorsys.hsv_to_rgb(h2, s2, v2)
    return int(cr * 255), int(cg * 255), int(cb * 255)


def random_color_pair() -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """
    Return (bg_rgb, fg_rgb) where bg is a random vivid color and fg is its
    HSV complement (hue +180°). Both are always colorful, always high contrast.
    Excludes near-black and near-white backgrounds.
    """
    import colorsys
    while True:
        # Generate in HSV for reliable saturation/value control
        h  = random.random()
        s  = random.uniform(0.5, 1.0)   # always vivid
        v  = random.uniform(0.35, 0.95) # not too dark or blown out
        r, g, b = (int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))
        fg = _complement_rgb(r, g, b)
        return (r, g, b), fg


def _make_cache_key(font_path: str, lines: tuple[str, ...],
                    usable_width: int, usable_height: int) -> str:
    lines_hash = hashlib.md5("||".join(lines).encode("utf-8")).hexdigest()
    return f"{font_path}|{lines_hash}|{usable_width}|{usable_height}"


def _load_font_size_cache() -> None:
    global _font_size_cache, _font_cache_dirty
    try:
        with open(_FONT_CACHE_PATH, 'r') as f:
            raw = json.load(f)
        # Scrub stale zero-size entries that predate the max(best,1) fix
        _font_size_cache = {k: v for k, v in raw.items() if v > 0}
        if len(_font_size_cache) < len(raw):
            _font_cache_dirty = True  # will be flushed at exit
    except FileNotFoundError:
        _font_size_cache = {}

def _save_font_size_cache() -> None:
    if _font_cache_dirty:
        with open(_FONT_CACHE_PATH, 'w') as f:
            json.dump(_font_size_cache, f)

atexit.register(_save_font_size_cache)


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
        if size <= 0:
            continue  # defensive: skip any zero entries that slipped through
        font_path = key.split("|")[0]
        pair = (font_path, size)
        if pair not in seen:
            seen.add(pair)
            _load_font_cached(font_path, size)


def _find_max_font_size_cached(font_path: str, lines: tuple[str, ...],
                               usable_width: int, usable_height: int) -> int:
    global _font_cache_dirty
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
    _font_cache_dirty = True
    return max(best, 1)


def _measure_block(font: FreeTypeFont | BitmapFont,
                   lines: list[str],
                   line_spacing: float = 1.5) -> tuple[int, int]:
    """Return (width, height) of a text block at the given font and spacing."""
    max_w, total_h = 0, 0
    for line in lines:
        bbox = _dummy_draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        max_w = max(max_w, w)
        total_h += int(h * line_spacing)
    return max_w, total_h


def _pick_layout_mode() -> str:
    modes, weights = zip(*_LAYOUT_MODES)
    return random.choices(modes, weights=weights, k=1)[0]


# ── Run once at import time ────────────────────────────────────────────────────
_load_font_size_cache()
_warm_font_cache()


# ── class ─────────────────────────────────────────────────────────────────────
class Text(DrawGenerator):
    """
    Utility Generator for drawing text on images.
    Provides canvas creation, dynamic font scaling, and text layout.
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

        half = lines[len(lines) // 2:]
        half_size = self._find_max_font_size(font_path, half)
        if half_size >= self.min_font_size:
            return half_size, half

        return max(size, self.min_font_size), lines

    def _font_size_for_tile_fraction(self, font_path: str, lines: list[str],
                                     fraction: float) -> int:
        """
        Find the largest font size that fits the text block within a fraction
        of the canvas height (e.g. 0.35 = fits in 35% of canvas height).
        Uses the full canvas width as the width constraint.
        """
        target_h = int(self.height * fraction)
        size = _find_max_font_size_cached(
            font_path, tuple(lines), self.usable_width, target_h
        )
        return max(size, self.min_font_size)

    def _draw_text_block(self, drawing: ImageDraw.ImageDraw,
                         lines: list[str],
                         font: FreeTypeFont | BitmapFont,
                         x: int, y: int,
                         fg_color: str,
                         line_spacing: float = 1.5) -> None:
        """Draw a block of lines starting at (x, y) with the given font and color."""
        cy = y
        for line in lines:
            bbox = drawing.textbbox((0, 0), str(line), font=font)
            h = bbox[3] - bbox[1]
            drawing.text((x, cy), line, fill=fg_color, font=font)
            cy += int(h * line_spacing)

    def _layout_tile(self,
                     img: Image.Image,
                     lines: list[str],
                     font_path: str,
                     bg_color: str,
                     fg_color: str) -> None:
        """
        Tile the text block across the full canvas with per-tile randomness:
          - Font sized to fill a random fraction of canvas height (25–45%)
          - Random position jitter per tile (±jitter_px)
          - Random skip probability per tile (~5–20%)
          - Random color pair per tile chosen from _TILE_COLORS,
            seeded from the caller's bg/fg so the palette stays coherent
        """
        # ── randomised parameters (one roll per image) ────────────────────────
        tile_fraction = random.uniform(0.25, 0.45)
        jitter_px     = random.randint(5, 25)
        skip_prob     = random.uniform(0.05, 0.20)
        line_spacing  = random.uniform(1.3, 1.7)
        color_mode    = random.choice(["fixed", "alternate", "random"])

        # Build a palette of random high-contrast pairs for this image.
        # bg_color is already an RGB tuple from generate_text_image.
        palette_size = random.randint(3, 7)
        palette: list[tuple[tuple[int, int, int], str]] = [
            random_color_pair() for _ in range(palette_size)
        ]
        palette[0] = (bg_color, fg_color)  # anchor with the canvas base color

        # ── font sizing ───────────────────────────────────────────────────────
        font_size = self._font_size_for_tile_fraction(font_path, lines, tile_fraction)
        font = _load_font_cached(font_path, font_size)

        block_w, block_h = _measure_block(font, lines, line_spacing)
        if block_w <= 0 or block_h <= 0:
            self.log.debug("Tile block has zero size; falling back to single draw.")
            drawing = ImageDraw.Draw(img)
            self._draw_text_block(drawing, lines, font, self.border_size,
                                  self.border_size, fg_color, line_spacing)
            return

        # ── tile grid ─────────────────────────────────────────────────────────
        # Add a small gap between tiles so they don't bleed into each other
        gap_x = max(8, block_w // 10)
        gap_y = max(6, block_h // 10)
        step_x = block_w + gap_x
        step_y = block_h + gap_y

        # Start one step before canvas edge so left/top tiles are partially visible
        start_x = -(block_w // 2)
        start_y = -(block_h // 2)

        drawing = ImageDraw.Draw(img)
        tile_index = 0

        y = start_y
        while y < self.height + block_h:
            x = start_x
            while x < self.width + block_w:
                # Random skip
                if random.random() < skip_prob:
                    x += step_x
                    tile_index += 1
                    continue

                # Jitter
                jx = random.randint(-jitter_px, jitter_px)
                jy = random.randint(-jitter_px, jitter_px)
                tx, ty = x + jx, y + jy

                # Color selection — palette entries are (rgb_tuple, fg_name)
                if color_mode == "fixed":
                    tile_bg, tile_fg = bg_color, fg_color
                elif color_mode == "alternate":
                    tile_bg, tile_fg = palette[tile_index % len(palette)]
                else:  # "random"
                    tile_bg, tile_fg = random.choice(palette)

                # Draw tile background rect, then text
                drawing.rectangle(
                    [tx, ty, tx + block_w, ty + block_h],
                    fill=tile_bg
                )
                self._draw_text_block(drawing, lines, font, tx, ty,
                                      tile_fg, line_spacing)

                x += step_x
                tile_index += 1
            y += step_y

    def _layout_hero(self,
                     img: Image.Image,
                     lines: list[str],
                     font_path: str,
                     base_bg: tuple[int, int, int],
                     base_fg: tuple[int, int, int]) -> None:
        """
        Hero layout: one large centered block fills most of the canvas,
        with smaller repeat blocks scattered in the remaining margins.
        Each block gets its own random complementary color pair.
        """
        line_spacing = random.uniform(1.3, 1.7)
        drawing = ImageDraw.Draw(img)

        # ── hero block ────────────────────────────────────────────────────────
        # Size to fill 65–85% of canvas height
        hero_fraction = random.uniform(0.65, 0.85)
        hero_size = self._font_size_for_tile_fraction(font_path, lines, hero_fraction)
        hero_font = _load_font_cached(font_path, hero_size)
        hero_w, hero_h = _measure_block(hero_font, lines, line_spacing)

        # Center the hero block
        hx = (self.width  - hero_w) // 2
        hy = (self.height - hero_h) // 2

        drawing.rectangle([hx, hy, hx + hero_w, hy + hero_h], fill=base_bg)
        self._draw_text_block(drawing, lines, hero_font, hx, hy, base_fg, line_spacing)

        # ── margin fill ───────────────────────────────────────────────────────
        # Small tiles sized to 15–25% of canvas height, scattered outside hero rect
        small_fraction = random.uniform(0.15, 0.25)
        small_size = self._font_size_for_tile_fraction(font_path, lines, small_fraction)
        small_font = _load_font_cached(font_path, small_size)
        small_w, small_h = _measure_block(small_font, lines, line_spacing)

        if small_w <= 0 or small_h <= 0:
            return

        skip_prob = random.uniform(0.1, 0.35)
        jitter_px = random.randint(0, 15)
        gap_x = max(6, small_w // 12)
        gap_y = max(4, small_h // 12)
        step_x = small_w + gap_x
        step_y = small_h + gap_y

        # Hero exclusion zone (with a small buffer so tiles don't clip the edge)
        buf = 10
        ex0, ey0 = hx - buf, hy - buf
        ex1, ey1 = hx + hero_w + buf, hy + hero_h + buf

        tile_index = 0
        y = -(small_h // 2)
        while y < self.height + small_h:
            x = -(small_w // 2)
            while x < self.width + small_w:
                # Skip tiles that overlap the hero block
                if not (x + small_w < ex0 or x > ex1 or
                        y + small_h < ey0 or y > ey1):
                    x += step_x
                    tile_index += 1
                    continue

                if random.random() < skip_prob:
                    x += step_x
                    tile_index += 1
                    continue

                jx = random.randint(-jitter_px, jitter_px)
                jy = random.randint(-jitter_px, jitter_px)
                tx, ty = x + jx, y + jy

                tile_bg, tile_fg = random_color_pair()
                drawing.rectangle([tx, ty, tx + small_w, ty + small_h], fill=tile_bg)
                self._draw_text_block(drawing, lines, small_font, tx, ty,
                                      tile_fg, line_spacing)

                x += step_x
                tile_index += 1
            y += step_y

    def _make_block_stamp(self,
                          lines: list[str],
                          font: FreeTypeFont | BitmapFont,
                          bg_color: tuple[int, int, int],
                          fg_color: tuple[int, int, int] | str,
                          block_w: int, block_h: int,
                          line_spacing: float) -> Image.Image:
        """Render one text block onto a transparent RGBA stamp for rotation/pasting."""
        stamp = Image.new("RGBA", (block_w, block_h), (*bg_color, 255))
        d = ImageDraw.Draw(stamp)
        cy = 0
        for line in lines:
            bbox = d.textbbox((0, 0), str(line), font=font)
            h = bbox[3] - bbox[1]
            d.text((0, cy), line, fill=fg_color, font=font)
            cy += int(h * line_spacing)
        return stamp

    def _layout_scatter(self,
                        img: Image.Image,
                        lines: list[str],
                        font_path: str,
                        base_bg: tuple[int, int, int],
                        base_fg: tuple[int, int, int]) -> None:
        """
        Scatter randomly rotated text blocks across the canvas.
          - Block size: 20–40% of canvas height
          - Rotation: ±45° per block
          - Count: enough to reach a target coverage ratio (60–90%)
          - Each block gets its own random_color_pair()
        """
        line_spacing   = random.uniform(1.3, 1.7)
        block_fraction = random.uniform(0.20, 0.40)
        target_coverage = random.uniform(0.60, 0.90)
        max_blocks     = 120  # hard cap so we never spin forever

        font_size = self._font_size_for_tile_fraction(font_path, lines, block_fraction)
        font      = _load_font_cached(font_path, font_size)
        block_w, block_h = _measure_block(font, lines, line_spacing)

        if block_w <= 0 or block_h <= 0:
            self.log.debug("Scatter block has zero size; skipping.")
            return

        canvas_area   = self.width * self.height
        block_area    = block_w * block_h
        target_area   = canvas_area * target_coverage
        # Estimate how many placements we need (blocks overlap, so overshoot a bit)
        n_blocks = min(max_blocks, max(8, int(target_area / block_area * 1.4)))

        img_rgba = img.convert("RGBA")

        for _ in range(n_blocks):
            angle = random.uniform(-45, 45)
            tile_bg, tile_fg = random_color_pair()

            stamp = self._make_block_stamp(
                lines, font, tile_bg, tile_fg, block_w, block_h, line_spacing
            )
            rotated = stamp.rotate(angle, expand=True, resample=Image.BICUBIC)
            rw, rh  = rotated.size

            # Allow blocks to hang off edges by up to half their size
            cx = random.randint(-rw // 2, self.width  + rw // 2)
            cy = random.randint(-rh // 2, self.height + rh // 2)
            # Paste top-left corner so center lands at (cx, cy)
            px, py = cx - rw // 2, cy - rh // 2

            img_rgba.paste(rotated, (px, py), rotated)

        # Merge back to RGB
        result = img_rgba.convert("RGB")
        img.paste(result)

    def _layout_columns(self,
                         img: Image.Image,
                         lines: list[str],
                         font_path: str,
                         base_bg: tuple[int, int, int],
                         base_fg: tuple[int, int, int]) -> None:
        """
        Columns layout: divide canvas into 2–4 vertical columns, each with its
        own background color. Text repeats top-to-bottom within each column until
        the column is full. Each column gets a fresh random_color_pair().
        """
        n_cols       = random.randint(2, 4)
        gutter       = random.randint(4, 20)
        line_spacing = random.uniform(1.3, 1.7)
        drawing      = ImageDraw.Draw(img)

        col_width = (self.width - gutter * (n_cols + 1)) // n_cols

        # Font sized to fit within one column width, up to 90% of canvas height
        target_h  = int(self.height * 0.90)
        font_size = _find_max_font_size_cached(
            font_path, tuple(lines), col_width - gutter, target_h
        )
        font_size = max(font_size, self.min_font_size)
        font      = _load_font_cached(font_path, font_size)

        _, block_h = _measure_block(font, lines, line_spacing)
        if block_h <= 0:
            self.log.debug("Columns block has zero height; skipping.")
            return

        for col in range(n_cols):
            col_bg, col_fg = random_color_pair()
            x0 = gutter + col * (col_width + gutter)
            x1 = x0 + col_width

            # Fill column background
            drawing.rectangle([x0, 0, x1, self.height], fill=col_bg)

            # Typeset text top-to-bottom, repeating the block to fill the column
            y = self.border_size
            while y < self.height:
                self._draw_text_block(
                    drawing, lines, font, x0 + 4, y, col_fg, line_spacing
                )
                y += block_h + gutter
                if y + block_h > self.height + block_h:
                    break

    def generate_text_image(self,
                            lines_to_draw: list[str],
                            language: str = "English",
                            bg_color: str = "black",
                            fg_color: str = "white") -> tuple[Image.Image, str]:
        """
        Create a full-canvas text image using a randomly selected layout mode.
        bg_color/fg_color params are ignored — colors are generated algorithmically.
        Returns (image, layout_mode) so callers can log the mode.
        """
        font_path = self.language_fonts.get(language, self.language_fonts["English"])
        base_bg, base_fg = random_color_pair()
        img = Image.new('RGB', (self.width, self.height), base_bg)

        mode = _pick_layout_mode()
        self.log.debug(f"Text layout mode: {mode}, base_bg={base_bg}")

        if mode == "tile":
            self._layout_tile(img, lines_to_draw, font_path, base_bg, base_fg)
        elif mode == "hero":
            self._layout_hero(img, lines_to_draw, font_path, base_bg, base_fg)
        elif mode == "scatter":
            self._layout_scatter(img, lines_to_draw, font_path, base_bg, base_fg)
        elif mode == "columns":
            self._layout_columns(img, lines_to_draw, font_path, base_bg, base_fg)
        else:
            self.log.debug(f"Unknown layout mode '{mode}', falling back to tile.")
            self._layout_tile(img, lines_to_draw, font_path, base_bg, base_fg)

        return img, mode
