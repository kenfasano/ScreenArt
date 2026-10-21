from .drawGenerator import DrawGenerator
<<<<<<< HEAD
from PIL import Image, ImageDraw
from enum import Enum
=======
from PIL import Image, ImageDraw 
>>>>>>> 13cbfdb469bfedc70094c84f240b666a122666e3
import math
import colorsys
import random
import os

<<<<<<< HEAD

class IllusionType(Enum):
    RAINBOW_GRID     = 1
    RAINBOW_SINGLE   = 2
    CONTRAST_SPIRAL  = 3
    PINWHEEL         = 4
    CONCENTRIC_RINGS = 5
    DUAL_SPIRAL      = 6
    COMET_LAYOUT     = 7
    GREYSCALE_STEPPED = 8


=======
>>>>>>> 13cbfdb469bfedc70094c84f240b666a122666e3
class PeripheralDriftIllusion(DrawGenerator):
    def __init__(self, out_dir: str):
        super().__init__(out_dir)
        self.file_count = self.config.get("file_counts", {}).get("peripheraldriftillusion", 20)
        self.base_filename = "peripheral_drift"

<<<<<<< HEAD
    # ------------------------------------------------------------------
    # Background helpers
    # ------------------------------------------------------------------

    def generate_gradient_background(
        self,
        width: int,
        height: int,
        color_top: tuple[int, int, int],
        color_bottom: tuple[int, int, int],
    ) -> Image.Image:
        """Vertical gradient background."""
        base = Image.new("RGB", (width, height), color_top)
        top = Image.new("RGB", (width, height), color_bottom)
        mask = Image.new("L", (width, height))
        mask_data: list[int] = []
        for y in range(height):
            alpha: int = int(255 * (y / height))
            mask_data.extend([alpha] * width)
=======
    def generate_gradient_background(self, width: int, height: int, color_top: tuple[int, int, int], color_bottom: tuple[int, int, int]) -> Image.Image:
        """Generates a vertical gradient background."""
        base = Image.new('RGB', (width, height), color_top)
        top = Image.new('RGB', (width, height), color_bottom)
        mask = Image.new('L', (width, height))
        mask_data = []
        
        for y in range(height):
            alpha: int = int(255 * (y / height))
            mask_data.extend([alpha] * width)
            
>>>>>>> 13cbfdb469bfedc70094c84f240b666a122666e3
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return base

<<<<<<< HEAD
    def generate_radial_gradient_background(
        self,
        width: int,
        height: int,
        color_center: tuple[int, int, int],
        color_edge: tuple[int, int, int],
    ) -> Image.Image:
        """Radial gradient — dark centre to lighter edge (or vice versa)."""
        img = Image.new("RGB", (width, height))
        pixels = img.load()
        cx, cy = width / 2, height / 2
        max_dist = math.hypot(cx, cy)
        for y in range(height):
            for x in range(width):
                t = math.hypot(x - cx, y - cy) / max_dist
                r = int(color_center[0] + t * (color_edge[0] - color_center[0]))
                g = int(color_center[1] + t * (color_edge[1] - color_center[1]))
                b = int(color_center[2] + t * (color_edge[2] - color_center[2]))
                pixels[x, y] = (r, g, b)  # type: ignore[index]
        return img

    # ------------------------------------------------------------------
    # Shared geometry helper
    # ------------------------------------------------------------------

    @staticmethod
    def _spiral_quad(
        cx: float,
        cy: float,
        r_inner_start: float,
        r_outer_start: float,
        r_inner_end: float,
        r_outer_end: float,
        angle_start: float,
        angle_end: float,
    ) -> list[tuple[int, int]]:
        return [
            (int(cx + r_outer_start * math.cos(angle_start)), int(cy + r_outer_start * math.sin(angle_start))),
            (int(cx + r_outer_end   * math.cos(angle_end)),   int(cy + r_outer_end   * math.sin(angle_end))),
            (int(cx + r_inner_end   * math.cos(angle_end)),   int(cy + r_inner_end   * math.sin(angle_end))),
            (int(cx + r_inner_start * math.cos(angle_start)), int(cy + r_inner_start * math.sin(angle_start))),
        ]

    # ------------------------------------------------------------------
    # CASE 1 & 2  –  original rainbow Archimedean spiral (kept, slightly
    #               cleaned up so the value range is correct: 0–1 not 0–255)
    # ------------------------------------------------------------------

    def create_spinning_optical_illusion(
        self,
        width: int = 800,
        height: int = 800,
        num_circles_x: int = 2,
        num_circles_y: int = 2,
        base_radius: int = 180,
        num_segments_per_turn: int = 40,
        num_turns: int = 6,
        spiral_tightness: float = 1.0,
        hue_start_offset: float = 0.0,
        hue_cycles: float = 2.0,
        bg_color_top: tuple[int, int, int] = (60, 40, 80),
        bg_color_bottom: tuple[int, int, int] = (10, 5, 20),
        alternate_direction: bool = False,
    ) -> Image.Image:
        img = self.generate_gradient_background(width, height, bg_color_top, bg_color_bottom)
        draw = ImageDraw.Draw(img)

        cx_step: float = width  / (num_circles_x + 1)
        cy_step: float = height / (num_circles_y + 1)
=======
    def create_spinning_optical_illusion(
        self, width: int = 800, height: int = 800,
        num_circles_x: int = 2, num_circles_y: int = 2,
        base_radius: int = 180, num_segments_per_turn: int = 40,
        num_turns: int = 6, spiral_tightness: float = 1.0,
        hue_start_offset: float = 0.0, hue_cycles: float = 2.0,
        bg_color_top: tuple[int, int, int] = (60, 40, 80),
        bg_color_bottom: tuple[int, int, int] = (10, 5, 20)
    ) -> Image.Image:
        
        img = self.generate_gradient_background(width, height, bg_color_top, bg_color_bottom)
        draw = ImageDraw.Draw(img)

        center_x_step: float = width / (num_circles_x + 1) if num_circles_x > 0 else width / 2
        center_y_step: float = height / (num_circles_y + 1) if num_circles_y > 0 else height / 2

>>>>>>> 13cbfdb469bfedc70094c84f240b666a122666e3
        total_segments: int = num_segments_per_turn * num_turns
        gap_per_turn = base_radius / num_turns
        snake_half_width = (gap_per_turn * 0.9) / 2

        for i in range(num_circles_x):
            for j in range(num_circles_y):
<<<<<<< HEAD
                cx = (i + 1) * cx_step
                cy = (j + 1) * cy_step
                direction = -1 if (alternate_direction and (i + j) % 2 == 1) else 1

                for s in range(total_segments):
                    progress      = s       / total_segments
                    next_progress = (s + 1) / total_segments

                    a0 = direction * math.radians(s       * (360 / num_segments_per_turn))
                    a1 = direction * math.radians((s + 1) * (360 / num_segments_per_turn))

                    rc0 = base_radius * (1 - progress)      * spiral_tightness
                    rc1 = base_radius * (1 - next_progress) * spiral_tightness

                    hue = (hue_start_offset + progress * hue_cycles) % 1.0
                    if s % 2 == 0:
                        r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 1.0)
                    else:
                        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 0.35)
                    color = (int(r * 255), int(g * 255), int(b * 255))

                    pts = self._spiral_quad(cx, cy,
                                            max(0, rc0 - snake_half_width),
                                            rc0 + snake_half_width,
                                            max(0, rc1 - snake_half_width),
                                            rc1 + snake_half_width,
                                            a0, a1)
                    draw.polygon(pts, fill=color)
        return img

    # ------------------------------------------------------------------
    # CASE 3  –  high-contrast B&W spiral with accent colour
    #            Classic luminance-contrast peripheral drift
    # ------------------------------------------------------------------

    def create_contrast_spiral(
        self,
        width: int = 800,
        height: int = 800,
        num_circles_x: int = 2,
        num_circles_y: int = 2,
        base_radius: int = 160,
        num_segments_per_turn: int = 48,
        num_turns: int = 5,
        accent_color: tuple[int, int, int] = (180, 60, 220),
        bg_color_top: tuple[int, int, int] = (18, 18, 18),
        bg_color_bottom: tuple[int, int, int] = (38, 38, 38),
    ) -> Image.Image:
        img = self.generate_gradient_background(width, height, bg_color_top, bg_color_bottom)
        draw = ImageDraw.Draw(img)
        cx_step = width  / (num_circles_x + 1)
        cy_step = height / (num_circles_y + 1)
        total   = num_segments_per_turn * num_turns
        hw      = (base_radius / num_turns * 0.9) / 2

        for i in range(num_circles_x):
            for j in range(num_circles_y):
                cx = (i + 1) * cx_step
                cy = (j + 1) * cy_step
                direction = -1 if (i + j) % 2 == 1 else 1  # alternate CW / CCW

                for s in range(total):
                    prog = s       / total
                    np_  = (s + 1) / total
                    a0   = direction * math.radians(s       * (360 / num_segments_per_turn))
                    a1   = direction * math.radians((s + 1) * (360 / num_segments_per_turn))
                    rc0  = base_radius * (1 - prog)
                    rc1  = base_radius * (1 - np_)

                    if s % 12 == 0:
                        color = accent_color
                    elif s % 2 == 0:
                        v = int(200 + 55 * prog)       # bright, gets slightly dimmer inward
                        color = (v, v, v)
                    else:
                        v = int(8 + 25 * prog)
                        color = (v, v, v)

                    pts = self._spiral_quad(cx, cy,
                                            max(0, rc0 - hw), rc0 + hw,
                                            max(0, rc1 - hw), rc1 + hw,
                                            a0, a1)
                    draw.polygon(pts, fill=color)
        return img

    # ------------------------------------------------------------------
    # CASE 4  –  pinwheel / starburst  (no spiral — radial blades)
    #            Each blade is bright on one edge, dark on the other,
    #            creating a strong rotational motion cue.
    # ------------------------------------------------------------------

    def create_pinwheel(
        self,
        width: int = 800,
        height: int = 800,
        num_circles_x: int = 2,
        num_circles_y: int = 2,
        base_radius: int = 160,
        num_blades: int = 24,
        hue: float = 0.6,
        bg_color_top: tuple[int, int, int] = (10, 10, 30),
        bg_color_bottom: tuple[int, int, int] = (30, 10, 50),
    ) -> Image.Image:
        img  = self.generate_gradient_background(width, height, bg_color_top, bg_color_bottom)
        draw = ImageDraw.Draw(img)
        cx_step = width  / (num_circles_x + 1)
        cy_step = height / (num_circles_y + 1)
        radial_steps = 12

        for i in range(num_circles_x):
            for j in range(num_circles_y):
                cx = (i + 1) * cx_step
                cy = (j + 1) * cy_step
                spin = 1 if (i + j) % 2 == 0 else -1

                for b in range(num_blades):
                    blade_frac = b / num_blades
                    a0 = spin * math.radians(blade_frac * 360)
                    a1 = spin * math.radians((blade_frac + 0.5 / num_blades) * 360)
                    a2 = spin * math.radians((blade_frac + 1.0 / num_blades) * 360)

                    blade_hue = (hue + blade_frac * 0.4) % 1.0

                    for rs in range(radial_steps):
                        r_frac  = rs       / radial_steps
                        r_frac1 = (rs + 1) / radial_steps
                        r0 = base_radius * r_frac
                        r1 = base_radius * r_frac1

                        # bright half
                        bright_val = 0.75 + 0.25 * r_frac
                        rb, gb, bb = colorsys.hsv_to_rgb(blade_hue, 0.15, bright_val)
                        bright = (int(rb * 255), int(gb * 255), int(bb * 255))
                        pts_b = [
                            (int(cx + r0 * math.cos(a0)), int(cy + r0 * math.sin(a0))),
                            (int(cx + r1 * math.cos(a0)), int(cy + r1 * math.sin(a0))),
                            (int(cx + r1 * math.cos(a1)), int(cy + r1 * math.sin(a1))),
                            (int(cx + r0 * math.cos(a1)), int(cy + r0 * math.sin(a1))),
                        ]
                        draw.polygon(pts_b, fill=bright)

                        # dark half
                        dark_val = 0.12 + 0.18 * r_frac
                        rd, gd, bd = colorsys.hsv_to_rgb(blade_hue, 0.9, dark_val)
                        dark = (int(rd * 255), int(gd * 255), int(bd * 255))
                        pts_d = [
                            (int(cx + r0 * math.cos(a1)), int(cy + r0 * math.sin(a1))),
                            (int(cx + r1 * math.cos(a1)), int(cy + r1 * math.sin(a1))),
                            (int(cx + r1 * math.cos(a2)), int(cy + r1 * math.sin(a2))),
                            (int(cx + r0 * math.cos(a2)), int(cy + r0 * math.sin(a2))),
                        ]
                        draw.polygon(pts_d, fill=dark)
        return img

    # ------------------------------------------------------------------
    # CASE 5  –  concentric rings (Fraser-spiral look)
    #            Rings with alternating light/dark arcs and a
    #            per-ring angular offset that makes them appear to spiral.
    # ------------------------------------------------------------------

    def create_concentric_rings(
        self,
        width: int = 800,
        height: int = 800,
        num_circles_x: int = 2,
        num_circles_y: int = 2,
        base_radius: int = 170,
        num_rings: int = 8,
        segments_per_ring: int = 36,
        hue: float = 0.55,
        bg_color_top: tuple[int, int, int] = (15, 20, 40),
        bg_color_bottom: tuple[int, int, int] = (5, 8, 20),
    ) -> Image.Image:
        img  = self.generate_gradient_background(width, height, bg_color_top, bg_color_bottom)
        draw = ImageDraw.Draw(img)
        cx_step = width  / (num_circles_x + 1)
        cy_step = height / (num_circles_y + 1)
        ring_width = base_radius / num_rings

        for i in range(num_circles_x):
            for j in range(num_circles_y):
                cx = (i + 1) * cx_step
                cy = (j + 1) * cy_step

                for ring in range(num_rings):
                    r_inner = ring       * ring_width
                    r_outer = (ring + 1) * ring_width
                    # phase offset per ring creates the false-spiral percept
                    phase_offset = ring * (math.pi / segments_per_ring)
                    ring_hue = (hue + ring * 0.06) % 1.0

                    for seg in range(segments_per_ring):
                        a0 = phase_offset + seg       * (2 * math.pi / segments_per_ring)
                        a1 = phase_offset + (seg + 1) * (2 * math.pi / segments_per_ring)

                        if seg % 2 == 0:
                            rr, gg, bb = colorsys.hsv_to_rgb(ring_hue, 0.6, 0.9)
                        else:
                            rr, gg, bb = colorsys.hsv_to_rgb(ring_hue, 1.0, 0.2)
                        color = (int(rr * 255), int(gg * 255), int(bb * 255))

                        pts = self._spiral_quad(cx, cy,
                                                r_inner, r_outer,
                                                r_inner, r_outer,
                                                a0, a1)
                        draw.polygon(pts, fill=color)
        return img

    # ------------------------------------------------------------------
    # CASE 6  –  dual complementary-hue spiral
    #            Two interleaved spirals in complementary colours —
    #            visually busy and very different from the single-hue cases.
    # ------------------------------------------------------------------

    def create_dual_spiral(
        self,
        width: int = 800,
        height: int = 800,
        num_circles_x: int = 1,
        num_circles_y: int = 2,
        base_radius: int = 200,
        num_segments_per_turn: int = 48,
        num_turns: int = 7,
        hue_a: float = 0.0,
        hue_b: float = 0.5,
        bg_color_top: tuple[int, int, int] = (10, 5, 10),
        bg_color_bottom: tuple[int, int, int] = (25, 10, 25),
    ) -> Image.Image:
        img  = self.generate_gradient_background(width, height, bg_color_top, bg_color_bottom)
        draw = ImageDraw.Draw(img)
        cx_step = width  / (num_circles_x + 1)
        cy_step = height / (num_circles_y + 1)
        total   = num_segments_per_turn * num_turns
        gap     = base_radius / num_turns
        hw      = (gap * 0.42) / 2   # thinner bands so both spirals fit

        for i in range(num_circles_x):
            for j in range(num_circles_y):
                cx = (i + 1) * cx_step
                cy = (j + 1) * cy_step

                for spiral_idx, hue_base in enumerate([hue_a, hue_b]):
                    # offset the second spiral by half a segment width radially
                    radial_offset = hw * 2.1 if spiral_idx == 1 else 0.0
                    # and rotate it by half a segment angularly
                    angle_offset  = math.radians(180 / num_segments_per_turn) if spiral_idx == 1 else 0.0

                    for s in range(total):
                        prog = s       / total
                        np_  = (s + 1) / total
                        a0   = angle_offset + math.radians(s       * (360 / num_segments_per_turn))
                        a1   = angle_offset + math.radians((s + 1) * (360 / num_segments_per_turn))
                        rc0  = base_radius * (1 - prog)  + radial_offset
                        rc1  = base_radius * (1 - np_)   + radial_offset

                        hue = (hue_base + prog * 1.5) % 1.0
                        val = 1.0 if s % 2 == 0 else 0.3
                        rr, gg, bb = colorsys.hsv_to_rgb(hue, 0.9, val)
                        color = (int(rr * 255), int(gg * 255), int(bb * 255))

                        pts = self._spiral_quad(cx, cy,
                                                max(0, rc0 - hw), rc0 + hw,
                                                max(0, rc1 - hw), rc1 + hw,
                                                a0, a1)
                        draw.polygon(pts, fill=color)
        return img

    # ------------------------------------------------------------------
    # CASE 7  –  asymmetric "comet" layout
    #            One large spiral off-centre plus a cluster of small ones —
    #            breaks the uniform grid entirely.
    # ------------------------------------------------------------------

    def create_comet_layout(
        self,
        width: int = 800,
        height: int = 800,
        hue_offset: float = 0.0,
        bg_color_top: tuple[int, int, int] = (5, 15, 30),
        bg_color_bottom: tuple[int, int, int] = (15, 5, 25),
    ) -> Image.Image:
        img  = self.generate_gradient_background(width, height, bg_color_top, bg_color_bottom)
        draw = ImageDraw.Draw(img)

        # big spiral, slightly off-centre
        self._draw_spiral_at(draw, cx=width * 0.38, cy=height * 0.42,
                             base_radius=220, num_segments_per_turn=52,
                             num_turns=7, hue_start=hue_offset,
                             hue_cycles=2.5, direction=1)

        # cluster of three small spirals
        small_positions = [
            (width * 0.74, height * 0.22, 0.33),
            (width * 0.78, height * 0.60, 0.66),
            (width * 0.62, height * 0.82, 0.12),
        ]
        for sx, sy, h_off in small_positions:
            self._draw_spiral_at(draw, cx=sx, cy=sy,
                                 base_radius=70, num_segments_per_turn=36,
                                 num_turns=4, hue_start=(hue_offset + h_off) % 1.0,
                                 hue_cycles=2.0, direction=-1)
        return img

    def _draw_spiral_at(
        self,
        draw: ImageDraw.ImageDraw,
        cx: float,
        cy: float,
        base_radius: int,
        num_segments_per_turn: int,
        num_turns: int,
        hue_start: float,
        hue_cycles: float,
        direction: int = 1,
    ) -> None:
        total  = num_segments_per_turn * num_turns
        gap    = base_radius / num_turns
        hw     = (gap * 0.9) / 2

        for s in range(total):
            prog = s       / total
            np_  = (s + 1) / total
            a0   = direction * math.radians(s       * (360 / num_segments_per_turn))
            a1   = direction * math.radians((s + 1) * (360 / num_segments_per_turn))
            rc0  = base_radius * (1 - prog)
            rc1  = base_radius * (1 - np_)

            hue = (hue_start + prog * hue_cycles) % 1.0
            val = 1.0 if s % 2 == 0 else 0.3
            rr, gg, bb = colorsys.hsv_to_rgb(hue, 0.85, val)
            color = (int(rr * 255), int(gg * 255), int(bb * 255))

            pts = self._spiral_quad(cx, cy,
                                    max(0, rc0 - hw), rc0 + hw,
                                    max(0, rc1 - hw), rc1 + hw,
                                    a0, a1)
            draw.polygon(pts, fill=color)

    # ------------------------------------------------------------------
    # CASE 8  –  monochrome stepped-value spiral
    #            Greyscale only, but each ring uses a different base
    #            brightness — strong depth cue, very different palette.
    # ------------------------------------------------------------------

    def create_greyscale_stepped_spiral(
        self,
        width: int = 800,
        height: int = 800,
        num_circles_x: int = 2,
        num_circles_y: int = 2,
        base_radius: int = 170,
        num_segments_per_turn: int = 44,
        num_turns: int = 6,
        bg_color_top: tuple[int, int, int] = (30, 30, 30),
        bg_color_bottom: tuple[int, int, int] = (8, 8, 8),
    ) -> Image.Image:
        img  = self.generate_gradient_background(width, height, bg_color_top, bg_color_bottom)
        draw = ImageDraw.Draw(img)
        cx_step = width  / (num_circles_x + 1)
        cy_step = height / (num_circles_y + 1)
        total   = num_segments_per_turn * num_turns
        gap     = base_radius / num_turns
        hw      = (gap * 0.9) / 2

        # brightness levels cycle across turns: light → dark → mid → ...
        turn_brightnesses = [220, 40, 150, 20, 180, 70]

        for i in range(num_circles_x):
            for j in range(num_circles_y):
                cx = (i + 1) * cx_step
                cy = (j + 1) * cy_step
                direction = -1 if (i + j) % 2 == 1 else 1

                for s in range(total):
                    prog = s       / total
                    np_  = (s + 1) / total
                    a0   = direction * math.radians(s       * (360 / num_segments_per_turn))
                    a1   = direction * math.radians((s + 1) * (360 / num_segments_per_turn))
                    rc0  = base_radius * (1 - prog)
                    rc1  = base_radius * (1 - np_)

                    turn_idx = int(prog * num_turns) % len(turn_brightnesses)
                    base_v   = turn_brightnesses[turn_idx]
                    # alternate light/dark within each turn band
                    v = min(255, base_v + 30) if s % 2 == 0 else max(0, base_v - 30)
                    color = (v, v, v)

                    pts = self._spiral_quad(cx, cy,
                                            max(0, rc0 - hw), rc0 + hw,
                                            max(0, rc1 - hw), rc1 + hw,
                                            a0, a1)
                    draw.polygon(pts, fill=color)
        return img

    # ------------------------------------------------------------------
    # run()
    # ------------------------------------------------------------------

    def run(self, *args, **kwargs) -> None:
        for i in range(self.file_count):
            hue_offset: float = (i * 0.125 * random.randint(1, 7)) % 1.0
            turns: int        = 5 + random.randint(1, 6)
            choice            = random.choice(list(IllusionType))
            img: Image.Image | None = None

            match choice:

                # --- original rainbow spiral, 2×2 grid, varied turns ---
                case IllusionType.RAINBOW_GRID:
                    img = self.create_spinning_optical_illusion(
                        width=800, height=800,
                        num_circles_x=2, num_circles_y=2,
                        base_radius=180, num_segments_per_turn=45,
                        num_turns=turns,
                        hue_start_offset=hue_offset, hue_cycles=3.0,
                        bg_color_top=(50 + (i * 20) % 160, 20, 60),
                        bg_color_bottom=(10, 5, 15),
                        alternate_direction=True,
                    )

                # --- original spiral, single large circle ---
                case IllusionType.RAINBOW_SINGLE:
                    img = self.create_spinning_optical_illusion(
                        width=800, height=800,
                        num_circles_x=1, num_circles_y=1,
                        base_radius=280, num_segments_per_turn=60,
                        num_turns=turns,
                        spiral_tightness=1.0,
                        hue_start_offset=hue_offset, hue_cycles=2.0,
                        bg_color_top=(70, 20, 20), bg_color_bottom=(20, 5, 5),
                        alternate_direction=False,
                    )

                # --- high-contrast B&W spiral, alternating CW/CCW ---
                case IllusionType.CONTRAST_SPIRAL:
                    accent_hue = (hue_offset + 0.3) % 1.0
                    ar, ag, ab = colorsys.hsv_to_rgb(accent_hue, 0.9, 0.85)
                    img = self.create_contrast_spiral(
                        width=800, height=800,
                        num_circles_x=2, num_circles_y=2,
                        base_radius=155, num_segments_per_turn=48,
                        num_turns=turns,
                        accent_color=(int(ar * 255), int(ag * 255), int(ab * 255)),
                    )

                # --- pinwheel / starburst ---
                case IllusionType.PINWHEEL:
                    img = self.create_pinwheel(
                        width=800, height=800,
                        num_circles_x=2, num_circles_y=2,
                        base_radius=160,
                        num_blades=24 + random.choice([0, 8, 16]),
                        hue=hue_offset,
                    )

                # --- concentric rings (Fraser-spiral look) ---
                case IllusionType.CONCENTRIC_RINGS:
                    img = self.create_concentric_rings(
                        width=800, height=800,
                        num_circles_x=2, num_circles_y=2,
                        base_radius=170,
                        num_rings=7 + random.randint(0, 4),
                        segments_per_ring=32 + random.choice([0, 8, 16]),
                        hue=hue_offset,
                        bg_color_top=(15, 20, 40), bg_color_bottom=(5, 8, 20),
                    )

                # --- dual complementary-hue interleaved spiral ---
                case IllusionType.DUAL_SPIRAL:
                    img = self.create_dual_spiral(
                        width=800, height=800,
                        num_circles_x=1, num_circles_y=2,
                        base_radius=200,
                        num_segments_per_turn=48, num_turns=turns,
                        hue_a=hue_offset,
                        hue_b=(hue_offset + 0.5) % 1.0,
                    )

                # --- asymmetric comet layout ---
                case IllusionType.COMET_LAYOUT:
                    bg_hue = (hue_offset + 0.6) % 1.0
                    bh_r, bh_g, bh_b = colorsys.hsv_to_rgb(bg_hue, 0.6, 0.08)
                    img = self.create_comet_layout(
                        width=800, height=800,
                        hue_offset=hue_offset,
                        bg_color_top=(int(bh_r * 255), int(bh_g * 255), int(bh_b * 255)),
                        bg_color_bottom=(5, 5, 12),
                    )

                # --- greyscale stepped-brightness spiral ---
                case IllusionType.GREYSCALE_STEPPED:
                    img = self.create_greyscale_stepped_spiral(
                        width=800, height=800,
                        num_circles_x=2, num_circles_y=2,
                        base_radius=170,
                        num_segments_per_turn=44, num_turns=turns,
                    )

            if img:
                filename = os.path.join(self.out_dir, f"{self.base_filename}_{i + 1}.jpeg")
=======
                center_x: int = int((i + 1) * center_x_step)
                center_y: int = int((j + 1) * center_y_step)

                for s in range(total_segments):
                    progress: float = s / total_segments
                    next_progress: float = (s + 1) / total_segments
                    
                    angle_start: float = math.radians(s * (360 / num_segments_per_turn))
                    angle_end: float = math.radians((s + 1) * (360 / num_segments_per_turn))

                    r_center_start: float = base_radius * (1 - progress) * spiral_tightness
                    r_center_end: float = base_radius * (1 - next_progress) * spiral_tightness

                    r_outer_start = r_center_start + snake_half_width
                    r_inner_start = max(0, r_center_start - snake_half_width)
                    r_outer_end = r_center_end + snake_half_width
                    r_inner_end = max(0, r_center_end - snake_half_width)
                    
                    current_hue_pos = (hue_start_offset + (progress * hue_cycles)) % 1.0
                    
                    if s % 2 == 0:
                        r, g, b = colorsys.hsv_to_rgb(current_hue_pos, 0.8, 255)
                    else:
                        r, g, b = colorsys.hsv_to_rgb(current_hue_pos, 1.0, 100)
                    
                    segment_color = (int(r), int(g), int(b))

                    x1_out = center_x + r_outer_start * math.cos(angle_start)
                    y1_out = center_y + r_outer_start * math.sin(angle_start)
                    x2_out = center_x + r_outer_end * math.cos(angle_end)
                    y2_out = center_y + r_outer_end * math.sin(angle_end)
                    x2_in = center_x + r_inner_end * math.cos(angle_end)
                    y2_in = center_y + r_inner_end * math.sin(angle_end)
                    x1_in = center_x + r_inner_start * math.cos(angle_start)
                    y1_in = center_y + r_inner_start * math.sin(angle_start)

                    points = [
                        (int(x1_out), int(y1_out)),
                        (int(x2_out), int(y2_out)),
                        (int(x2_in), int(y2_in)),
                        (int(x1_in), int(y1_in))
                    ]
                    draw.polygon(points, fill=segment_color)

        return img

    def run(self, *args, **kwargs):
        for i in range(self.file_count):
            turns: int = 6 + random.randint(1,6)
            hue_offset: float = (i * 0.125 * random.randint(1,7)) % 1.0 
                
            choice = random.randint(1,4)
            img: Image.Image | None = None 

            match choice:
                case 1:
                    img = self.create_spinning_optical_illusion(
                        width=800, height=800, num_circles_x=2, num_circles_y=2,
                        base_radius=180, num_segments_per_turn=45, num_turns=turns,
                        hue_start_offset=hue_offset, hue_cycles=3.0, 
                        bg_color_top=(50 + (i*20), 20, 60), bg_color_bottom=(10, 5, 15)
                    )
                case 2:
                    img = self.create_spinning_optical_illusion(
                        width=800, height=800, num_circles_x=2, num_circles_y=2,
                        base_radius=120, num_segments_per_turn=40, num_turns=3,              
                        spiral_tightness=1.0, hue_start_offset=0.0, hue_cycles=2.0,           
                        bg_color_top=(80, 60, 20), bg_color_bottom=(20, 10, 0)
                    )
                case 3:
                    img = self.create_spinning_optical_illusion(
                        width=800, height=800, num_circles_x=3, num_circles_y=3,
                        base_radius=80, num_segments_per_turn=50, num_turns=4,              
                        spiral_tightness=0.8, hue_start_offset=0.125, hue_cycles=2.0,           
                        bg_color_top=(20, 30, 70), bg_color_bottom=(5, 10, 20)
                    )
                case 4:
                    img = self.create_spinning_optical_illusion(
                        width=800, height=800, num_circles_x=1, num_circles_y=1,
                        base_radius=250, num_segments_per_turn=60, num_turns=2,              
                        spiral_tightness=1.0, hue_start_offset=0.25, hue_cycles=2.0,           
                        bg_color_top=(70, 20, 20), bg_color_bottom=(20, 5, 5)
                    )

            if img:
                filename = os.path.join(self.out_dir, f"{self.base_filename}_{i+1}.jpeg")
>>>>>>> 13cbfdb469bfedc70094c84f240b666a122666e3
                try:
                    img.save(filename, quality=95)
                    self.log.debug(f"Saved Optical Illusion: {filename}")
                except Exception as e:
                    self.log.debug(f"Failed to save {filename}: {e}")
