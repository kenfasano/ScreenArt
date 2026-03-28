import random
import math
import numpy as np
from PIL import Image, ImageDraw
from .drawGenerator import DrawGenerator


class MandalaDraw(DrawGenerator):
    """
    Procedurally generates colourful mandala images using polar-coordinate
    primitives: rose curves, polygon rings, arc bursts, and dot rings.

    Each image picks:
      - a random N-fold symmetry order (8, 12, 16)
      - a random base hue and hue-step for the palette
      - a random stack of 4-7 layers, each a different primitive type

    Output is wallpaper-quality JPEG at the configured width/height.
    """

    SYMMETRY_OPTIONS = [8, 8, 12, 12, 16]  # weights toward 8 and 12
    PRIMITIVE_TYPES  = ["rose", "polygon", "arc_burst", "dot_ring"]

    def __init__(self) -> None:
        super().__init__()
        cfg           = self.config.get("mandala_draw", {})
        self.width    = int(cfg.get("width",  self.config.get("mandala_draw", {}).get("width",  1920)))
        self.height   = int(cfg.get("height", self.config.get("mandala_draw", {}).get("height", 1280)))
        self.file_count = int(
            self.config.get("file_counts", {}).get("mandala_draw", 1)
        )
        self.base_filename = "mandala_draw"

    # ------------------------------------------------------------------
    # Palette helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
        """h in [0, 360), s and v in [0, 1]. Returns (r, g, b) in [0, 255]."""
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        sector = int(h / 60)
        rgb_map = [
            (c, x, 0), (x, c, 0), (0, c, x),
            (0, x, c), (x, 0, c), (c, 0, x),
        ]
        r, g, b = rgb_map[sector % 6]
        return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

    def _palette(
        self,
        n_layers: int,
        base_hue: float,
        hue_step: float,
        saturation: float = 0.85,
    ) -> list[tuple[int, int, int]]:
        """Return one rich colour per layer, rotating around the hue wheel."""
        colours: list[tuple[int, int, int]] = []
        for i in range(n_layers):
            hue = (base_hue + i * hue_step) % 360
            value = random.uniform(0.75, 1.0)
            colours.append(self._hsv_to_rgb(hue, saturation, value))
        return colours

    # ------------------------------------------------------------------
    # Polar → canvas coordinate helper
    # ------------------------------------------------------------------

    def _polar_to_xy(
        self, r: float, theta: float, cx: float, cy: float
    ) -> tuple[float, float]:
        return cx + r * math.cos(theta), cy + r * math.sin(theta)

    # ------------------------------------------------------------------
    # Primitives  (all accept N-fold symmetry, colour, draw handle)
    # ------------------------------------------------------------------

    def _draw_rose(
        self,
        draw: ImageDraw.ImageDraw,
        cx: float,
        cy: float,
        radius: float,
        symmetry: int,
        colour: tuple[int, int, int],
        alpha: int = 200,
    ) -> None:
        """
        Rose curve  r = radius · |cos(k · θ)|  where k = symmetry // 2.
        Produces `symmetry` petals when symmetry is even.
        """
        k = symmetry // 2
        steps = 720
        colour_a = colour + (alpha,)
        points: list[tuple[float, float]] = []
        for i in range(steps + 1):
            theta = 2 * math.pi * i / steps
            r = radius * abs(math.cos(k * theta))
            points.append(self._polar_to_xy(r, theta, cx, cy))
        if len(points) >= 2:
            draw.polygon(points, fill=colour_a, outline=None)

    def _draw_polygon_ring(
        self,
        draw: ImageDraw.ImageDraw,
        cx: float,
        cy: float,
        radius: float,
        symmetry: int,
        colour: tuple[int, int, int],
        thickness: int = 6,
        alpha: int = 220,
    ) -> None:
        """N-sided polygon outline, rotated by a random phase."""
        phase = random.uniform(0, 2 * math.pi / symmetry)
        colour_a = colour + (alpha,)
        pts = [
            self._polar_to_xy(
                radius, phase + 2 * math.pi * i / symmetry, cx, cy
            )
            for i in range(symmetry)
        ]
        draw.polygon(pts, fill=None, outline=colour_a, width=thickness)

    def _draw_arc_burst(
        self,
        draw: ImageDraw.ImageDraw,
        cx: float,
        cy: float,
        r_inner: float,
        r_outer: float,
        symmetry: int,
        colour: tuple[int, int, int],
        thickness: int = 4,
        alpha: int = 200,
    ) -> None:
        """N radial line segments from r_inner to r_outer."""
        colour_a = colour + (alpha,)
        phase = random.uniform(0, 2 * math.pi / symmetry)
        for i in range(symmetry):
            theta = phase + 2 * math.pi * i / symmetry
            x0, y0 = self._polar_to_xy(r_inner, theta, cx, cy)
            x1, y1 = self._polar_to_xy(r_outer, theta, cx, cy)
            draw.line([(x0, y0), (x1, y1)], fill=colour_a, width=thickness)

    def _draw_dot_ring(
        self,
        draw: ImageDraw.ImageDraw,
        cx: float,
        cy: float,
        radius: float,
        symmetry: int,
        colour: tuple[int, int, int],
        dot_radius: float = 12.0,
        alpha: int = 230,
    ) -> None:
        """N filled circles equally spaced on a ring of given radius."""
        colour_a = colour + (alpha,)
        phase = random.uniform(0, 2 * math.pi / symmetry)
        for i in range(symmetry):
            theta = phase + 2 * math.pi * i / symmetry
            x, y = self._polar_to_xy(radius, theta, cx, cy)
            r = dot_radius
            draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=colour_a)

    # ------------------------------------------------------------------
    # Background
    # ------------------------------------------------------------------

    def _draw_background(
        self,
        draw: ImageDraw.ImageDraw,
        cx: float,
        cy: float,
        max_r: float,
        base_colour: tuple[int, int, int],
    ) -> None:
        """Radial-ish background: a dark desaturated version of the base hue."""
        # Very dark background so colours pop
        bg = tuple(max(0, c // 8) for c in base_colour)
        draw.rectangle([0, 0, self.width, self.height], fill=bg)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Single mandala image
    # ------------------------------------------------------------------

    def _generate_one(self, index: int, out_dir: str) -> str:
        symmetry = random.choice(self.SYMMETRY_OPTIONS)
        cx       = self.width  / 2.0
        cy       = self.height / 2.0
        max_r    = min(cx, cy) * 0.92          # largest ring fits in frame

        # Palette
        base_hue = random.uniform(0, 360)
        hue_step = random.choice([15, 20, 25, 30, 45])
        n_layers = random.randint(5, 8)
        palette  = self._palette(n_layers, base_hue, hue_step)

        # Radii: evenly divide max_r across layers (inner → outer)
        radii = [max_r * (i + 1) / n_layers for i in range(n_layers)]

        # Build image with RGBA so alpha compositing works
        img  = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 255))
        draw = ImageDraw.Draw(img, "RGBA")

        self._draw_background(draw, cx, cy, max_r, palette[0])

        # Shuffle which primitive each layer uses; keep variety
        primitives = (self.PRIMITIVE_TYPES * 3)[:n_layers]
        random.shuffle(primitives)

        thickness_base = max(3, self.width // 400)

        for i, (ptype, radius, colour) in enumerate(
            zip(primitives, radii, palette)
        ):
            r_inner = radius * 0.7
            r_outer = radius

            if ptype == "rose":
                self._draw_rose(draw, cx, cy, radius, symmetry, colour)

            elif ptype == "polygon":
                # Optionally draw two nested polygons for richness
                self._draw_polygon_ring(
                    draw, cx, cy, radius, symmetry, colour,
                    thickness=thickness_base * 2,
                )
                inner_colour = palette[(i + 2) % n_layers]
                self._draw_polygon_ring(
                    draw, cx, cy, radius * 0.85, symmetry, inner_colour,
                    thickness=thickness_base,
                )

            elif ptype == "arc_burst":
                self._draw_arc_burst(
                    draw, cx, cy, r_inner, r_outer, symmetry, colour,
                    thickness=thickness_base,
                )

            elif ptype == "dot_ring":
                dot_r = max(6.0, radius / (symmetry * 1.2))
                self._draw_dot_ring(
                    draw, cx, cy, radius, symmetry, colour,
                    dot_radius=dot_r,
                )

        # Centre dot — anchors the composition
        centre_colour = palette[n_layers // 2]
        centre_r = max_r * 0.06
        draw.ellipse(
            [(cx - centre_r, cy - centre_r), (cx + centre_r, cy + centre_r)],
            fill=centre_colour + (255,),
        )

        # Convert to RGB JPEG
        rgb = img.convert("RGB")
        import os
        filename = f"{self.base_filename}_{index}.jpeg"
        out_path = os.path.join(out_dir, filename)
        rgb.save(out_path, "JPEG", quality=95)
        self.log.debug(f"Generated {out_path}  symmetry={symmetry}  layers={n_layers}")
        return out_path

    # ------------------------------------------------------------------
    # Generator entry point
    # ------------------------------------------------------------------

    def run(self, *args, **kwargs) -> int:
        import os
        import shutil

        out_dir = os.path.join(
            self.config["paths"]["generators_in"], "mandala_draw"
        )
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(out_dir, exist_ok=True)

        generated = 0
        for i in range(self.file_count):
            try:
                self._generate_one(i, out_dir)
                generated += 1
            except Exception as e:
                self.log.warning(f"mandala_draw: failed on image {i}: {e}")

        self.log.info(f"mandala_draw: generated {generated}/{self.file_count}")
        return generated
