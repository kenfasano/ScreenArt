import os
import numpy as np
from numba import njit
import random
from PIL import Image
#from concurrent.futures import ProcessPoolExecutor, as_completed
from numpy.typing import NDArray
from typing import Callable, Tuple
from .drawGenerator import DrawGenerator

HSVArrays = Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]
ModeFunc = Callable[
    [float, NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]],
    HSVArrays,
]

@njit(fastmath=True, cache=True)
def _draw_bubbles_jit(
    canvas,
    xi,
    yi,
    ri,
    colors_rgb,
    add_highlights,
):
    height = canvas.shape[0]
    width  = canvas.shape[1]
    count  = xi.shape[0]

    for i in range(count):
        cx = xi[i]
        cy = yi[i]
        r  = ri[i]

        r2 = r * r

        # Cache color locally (huge win vs indexing each pixel)
        c0 = colors_rgb[i, 0]
        c1 = colors_rgb[i, 1]
        c2 = colors_rgb[i, 2]

        y_min = 0 if cy - r < 0 else cy - r
        y_max = height if cy + r + 1 > height else cy + r + 1
        x_min = 0 if cx - r < 0 else cx - r
        x_max = width  if cx + r + 1 > width  else cx + r + 1

        for y in range(y_min, y_max):
            dy = y - cy
            dy2 = dy * dy

            row = canvas[y]  # avoid 2D indexing cost

            for x in range(x_min, x_max):
                dx = x - cx
                if dx * dx + dy2 <= r2:
                    row[x, 0] = c0
                    row[x, 1] = c1
                    row[x, 2] = c2

        if add_highlights:
            high_r = max(1, r // 4)
            high_r2 = high_r * high_r

            hx = cx - r // 3
            hy = cy - r // 3

            hy_min = 0 if hy - high_r < 0 else hy - high_r
            hy_max = height if hy + high_r + 1 > height else hy + high_r + 1
            hx_min = 0 if hx - high_r < 0 else hx - high_r
            hx_max = width  if hx + high_r + 1 > width  else hx + high_r + 1

            for y in range(hy_min, hy_max):
                dy = y - hy
                dy2 = dy * dy
                row = canvas[y]

                for x in range(hx_min, hx_max):
                    dx = x - hx
                    if dx * dx + dy2 <= high_r2:
                        row[x, 0] = 255
                        row[x, 1] = 255
                        row[x, 2] = 255

class Bubbles(DrawGenerator):
    def __init__(self):
        super().__init__()
        
        # Standard Configuration
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = 10 
        
        # Bubbles Specific
        self.min_radius = int(self.config.get('min_radius', 10))
        self.max_radius = int(self.config.get('max_radius', 60))
        self.base_filename = "bubbles"

        self.math_modes = ['random', 'radial_flip', 'radial_rainbow']
        self.theme_modes = ['fire']
        self.mode_map: dict[str, ModeFunc] = {
            "radial_flip": self._mode_radial_flip,
            "radial_rainbow": self._mode_radial_rainbow,
            "fire": self._mode_fire,
        }
        self.all_modes = list(self.mode_map.keys())

    def _hsv_to_rgb_vectorized(
        self,
        h: NDArray[np.float64],
        s: NDArray[np.float64],
        v: NDArray[np.float64],
    ) -> NDArray[np.uint8]:
        """
        Processes thousands of colors simultaneously using NumPy matrix math.
        """
        h = h % 1.0
        i = (h * 6.0).astype(int)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        
        i = i % 6
        conditions = [i == 0, i == 1, i == 2, i == 3, i == 4, i == 5]
        
        r = np.select(conditions, [v, q, p, p, t, v])
        g = np.select(conditions, [t, v, v, q, p, p])
        b = np.select(conditions, [p, p, t, v, v, q])
        
        return np.stack((r * 255, g * 255, b * 255), axis=-1).astype(np.uint8)

    def _mode_radial_flip(
        self,
        base_hue: float,
        norm_dist: NDArray[np.float64],
        jitters: NDArray[np.float64],
        s_rnds: NDArray[np.float64],
        v_rnds: NDArray[np.float64],
    ) -> HSVArrays:
        h = (base_hue + (norm_dist * 0.5)) % 1.0
        s = 0.8 + s_rnds
        v = 0.9 + v_rnds
        return h, s, v

    def _mode_radial_rainbow(
        self,
        base_hue: float,
        norm_dist: NDArray[np.float64],
        jitters: NDArray[np.float64],
        s_rnds: NDArray[np.float64],
        v_rnds: NDArray[np.float64],
    ) -> HSVArrays:
        h = (base_hue + norm_dist) % 1.0
        s = 0.8 + s_rnds
        v = 0.9 + v_rnds
        return h, s, v

    def _mode_fire(
        self,
        base_hue: float,
        norm_dist: NDArray[np.float64],
        jitters: NDArray[np.float64],
        s_rnds: NDArray[np.float64],
        v_rnds: NDArray[np.float64],
    ) -> HSVArrays:
        h = np.minimum(0.15, np.abs(jitters) * 1.5)
        s = 0.8 + np.abs(s_rnds)
        v = 0.8 + np.abs(v_rnds)
        return h, s, v

    def draw_bubbles(self, width, height, add_highlights=False):
        cx = width / 2
        cy = height / 2

        # --- AREA BUDGET ---
        target_pixels = width * height * random.uniform(0.4, 0.7)

        xs = []
        ys = []
        rs = []

        total_area = 0.0

        max_dist = max(1, np.sqrt(cx * cx + cy * cy))

        while total_area < target_pixels:
            x = random.uniform(0, width)
            y = random.uniform(0, height)

            dx = x - cx
            dy = y - cy
            norm_dist = np.sqrt(dx * dx + dy * dy) / max_dist

            base_r = self.max_radius - (self.max_radius - self.min_radius) * norm_dist

            # your aesthetically pleasing skew
            variance = random.random() ** 2 * 0.5 + 0.75
            r = int(max(1, base_r * variance))

            xs.append(int(x))
            ys.append(int(y))
            rs.append(r)

            total_area += np.pi * r * r

        count = len(rs)

        xi = np.array(xs, dtype=np.int32)
        yi = np.array(ys, dtype=np.int32)
        ri = np.array(rs, dtype=np.int32)

        mode = random.choice(self.all_modes)
        base_hue = random.random()

        # For mode functions we need norm_dist per bubble
        dx = xi - cx
        dy = yi - cy
        distances = np.sqrt(dx * dx + dy * dy)
        max_dist = max(1, np.sqrt(cx * cx + cy * cy))
        norm_dist = distances / max_dist

        jitters = np.random.uniform(-0.05, 0.05, count)
        s_rnds = np.random.uniform(-0.1, 0.1, count)
        v_rnds = np.random.uniform(-0.1, 0.1, count)

        h, s, v = self.mode_map[mode](
            base_hue,
            norm_dist,
            jitters,
            s_rnds,
            v_rnds,
        )

        s = np.clip(s, 0.0, 1.0)
        v = np.clip(v, 0.0, 1.0)

        colors_rgb = self._hsv_to_rgb_vectorized(h, s, v)

        # Canvas
        canvas = np.zeros((height, width, 3), dtype=np.uint8)

        _draw_bubbles_jit(
            canvas,
            xi,
            yi,
            ri,
            colors_rgb,
            add_highlights,
        )

        return Image.fromarray(canvas, 'RGB')

    def run(self, *args, **kwargs) -> None:
        """
        Multiprocessing generation loop with execution timing.
        """

        with self.timer():
            out_dir = os.path.join(self.config["paths"]["generators_in"], "bubbles")
            os.makedirs(out_dir, exist_ok=True)
            for i in range(self.file_count):
                img = self.draw_bubbles(self.width, self.height)
                if img:
                    # Create a unique filename for each image
                    filename = os.path.join(out_dir, f"{self.base_filename}_{i+1}.jpeg")
                    # Save the image with the specified filename
                    img.save(filename, quality=95)
