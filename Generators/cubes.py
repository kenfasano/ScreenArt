import math
import random
import colorsys
import os
from PIL import Image, ImageDraw, ImageChops
from .drawGenerator import DrawGenerator


def _shade(rgb: tuple[int,int,int], factor: float) -> tuple[int,int,int]:
    """Multiply RGB brightness by factor, clamped to [0,255]."""
    return (
        max(0, min(255, int(rgb[0] * factor))),
        max(0, min(255, int(rgb[1] * factor))),
        max(0, min(255, int(rgb[2] * factor))),
    )


def _isometric_faces(
    cx: float, cy: float, size: float
) -> tuple[list, list, list]:
    """
    Return (top, left, right) face polygons for an isometric cube
    centred at (cx, cy) with given size.

    Isometric axes (screen coords):
      right  = (+cos30,  +sin30)  = (+√3/2, +0.5)
      left   = (-cos30,  +sin30)  = (-√3/2, +0.5)
      up     = (0, -1)
    """
    s = size / 2
    c30 = math.sqrt(3) / 2  # cos 30°
    s30 = 0.5               # sin 30°

    # 8 vertices of the cube in isometric projection
    # top-face corners (y offset = -s in the "up" axis)
    top_y = cy - s  # apex of top face

    # top face: diamond at the top
    top = [
        (cx,          top_y - s * 1.0),   # top point
        (cx + s*c30,  top_y - s * s30),   # right
        (cx,          top_y),              # bottom (shared)
        (cx - s*c30,  top_y - s * s30),   # left
    ]

    # left face: parallelogram going down-left
    left = [
        (cx - s*c30,  top_y - s*s30),     # top-right of left face
        (cx,          top_y),              # top-center
        (cx,          top_y + s),          # bottom-center
        (cx - s*c30,  top_y - s*s30 + s), # bottom-left
    ]

    # right face: parallelogram going down-right
    right = [
        (cx,          top_y),              # top-center
        (cx + s*c30,  top_y - s*s30),     # top-right
        (cx + s*c30,  top_y - s*s30 + s), # bottom-right
        (cx,          top_y + s),          # bottom-center
    ]

    return top, left, right


def _perspective_faces(
    cx: float, cy: float, size: float,
    vx: float, vy: float, vz: float = 600.0
) -> tuple[list, list, list]:
    """
    Return (top, left, right) face polygons for a perspective-projected cube
    centred at (cx, cy) with given size, vanishing point at (vx, vy).

    We define 8 3D corners, project each to 2D, then select the three visible
    faces based on which side the vanishing point is on.
    """
    h = size / 2

    # 3D cube corners (local coords, y-up)
    corners_3d = [
        (-h, -h, -h), ( h, -h, -h), ( h,  h, -h), (-h,  h, -h),  # back face
        (-h, -h,  h), ( h, -h,  h), ( h,  h,  h), (-h,  h,  h),  # front face
    ]

    # Simple perspective: project onto screen with focal length vz
    def proj(x3, y3, z3):
        scale = vz / (vz + z3 + h * 2)
        return (cx + x3 * scale, cy - y3 * scale)

    p = [proj(x, y, z) for x, y, z in corners_3d]

    # Faces: indices into corners
    # top face (y = +h): corners 2,3,7,6  (back-top-right, back-top-left, front-top-left, front-top-right)
    top   = [p[3], p[2], p[6], p[7]]
    # front face (z = +h): corners 4,5,6,7
    front = [p[4], p[5], p[6], p[7]]
    # right face (x = +h): corners 1,2,6,5
    right = [p[1], p[2], p[6], p[5]]
    # left face (x = -h): corners 0,3,7,4
    left  = [p[0], p[3], p[7], p[4]]

    # Choose visible side faces based on vanishing point position
    if vx >= cx:
        side_a = right
    else:
        side_a = left

    return top, side_a, front


class Cubes(DrawGenerator):
    def __init__(self):
        super().__init__()

        self.width  = int(self.config.get('width',  1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = int(self.config.get('file_count', 6))
        self.base_filename = "cubes"

        self.loops    = int(self.config.get('loops',    2000))
        self.min_size = int(self.config.get('min_size',   25))
        self.max_size = int(self.config.get('max_size',  200))

        self.color_modes = [
            'random', 'radial_rainbow', 'radial_flip',
            'fire', 'cool', 'grayscale'
        ]
        # Projection styles chosen randomly per image
        self.proj_modes = ['isometric', 'perspective']

        # Face shading factors: top / side-a / side-b
        # Isometric: top brightest, left/right darker
        self._iso_shading   = (1.00, 0.55, 0.75)
        # Perspective: top bright, front mid, side varies
        self._persp_shading = (1.00, 0.70, 0.85)

    def get_color(self, mode: str, norm_dist: float, base_hue: float) -> tuple[int,int,int]:
        h, s, v = 0.0, random.uniform(0.6, 1.0), random.uniform(0.7, 1.0)

        if mode == 'random':
            h = random.random()
        elif mode == 'radial_rainbow':
            h = (base_hue + norm_dist) % 1.0
        elif mode == 'radial_flip':
            h = (base_hue + norm_dist * 0.5) % 1.0
        elif mode == 'fire':
            h = random.uniform(0.98, 1.15) % 1.0
            s = random.uniform(0.8, 1.0)
        elif mode == 'cool':
            h = random.uniform(0.5, 0.85)
        elif mode == 'grayscale':
            s = 0.0
            v = random.uniform(0.2, 0.95)

        if mode not in ('grayscale', 'fire'):
            s = max(0.5, min(1.0, s))
            v = max(0.6, min(1.0, v))

        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r*255), int(g*255), int(b*255))

    def _draw_cube(self,
                   draw: ImageDraw.ImageDraw,
                   mask_draw: ImageDraw.ImageDraw,
                   cx: float, cy: float, size: float,
                   color: tuple[int,int,int],
                   proj: str,
                   vp: tuple[float,float]) -> None:
        """Draw a 3-face shaded cube and update the mask."""
        if proj == 'isometric':
            top, face_a, face_b = _isometric_faces(cx, cy, size)
            sf = self._iso_shading
        else:
            top, face_a, face_b = _perspective_faces(cx, cy, size, vp[0], vp[1])
            sf = self._persp_shading

        c_top   = _shade(color, sf[0])
        c_a     = _shade(color, sf[1])
        c_b     = _shade(color, sf[2])

        draw.polygon(top,    fill=c_top)
        draw.polygon(face_a, fill=c_a)
        draw.polygon(face_b, fill=c_b)

        mask_draw.polygon(top,    fill=1)
        mask_draw.polygon(face_a, fill=1)
        mask_draw.polygon(face_b, fill=1)

    def run(self, *args, **kwargs) -> None:
        img_cx = self.width  / 2
        img_cy = self.height / 2
        max_dist = math.sqrt(img_cx**2 + img_cy**2) or 1

        out_dir = os.path.join(self.config["paths"]["generators_in"], "cubes")
        os.makedirs(out_dir, exist_ok=True)

        for i in range(self.file_count):
            color_mode = random.choice(self.color_modes)
            proj_mode  = random.choice(self.proj_modes)
            base_hue   = random.random()

            # Vanishing point for perspective: random offset from canvas center
            vp = (
                img_cx + random.uniform(-self.width  * 0.4, self.width  * 0.4),
                img_cy + random.uniform(-self.height * 0.4, self.height * 0.4),
            )

            img  = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            mask      = Image.new('1', (self.width, self.height), 0)
            mask_draw = ImageDraw.Draw(mask)

            placed_count = 0

            for _ in range(self.loops):
                size   = random.randint(self.min_size, self.max_size)
                margin = int(size * 0.75)
                cx = random.randint(margin, self.width  - margin)
                cy = random.randint(margin, self.height - margin)

                # Bounding-box overlap check against mask
                half = int(size * 0.9)
                bbox = (
                    max(0, cx - half), max(0, cy - half),
                    min(self.width,  cx + half + 1),
                    min(self.height, cy + half + 1),
                )
                if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
                    continue

                mask_crop = mask.crop(bbox)
                if mask_crop.getbbox():   # any pixel already set → skip
                    continue

                dist      = math.sqrt((cx - img_cx)**2 + (cy - img_cy)**2)
                norm_dist = dist / max_dist
                color     = self.get_color(color_mode, norm_dist, base_hue)

                self._draw_cube(draw, mask_draw, cx, cy, size,
                                color, proj_mode, vp)
                placed_count += 1

            filename = os.path.join(out_dir, f"{self.base_filename}_{i+1}.jpeg")
            try:
                img.save(filename, quality=95)
                self.log.debug(f"proj={proj_mode} color={color_mode} placed={placed_count}")
            except Exception as e:
                self.log.debug(f"Failed to save {filename}: {e}")
