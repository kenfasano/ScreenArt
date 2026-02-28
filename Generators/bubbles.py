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
    height, width, _ = canvas.shape
    count = xi.shape[0]

    for i in range(count):
        cx = xi[i]
        cy = yi[i]
        r = ri[i]

        y_min = max(0, cy - r)
        y_max = min(height, cy + r + 1)
        x_min = max(0, cx - r)
        x_max = min(width, cx + r + 1)

        r2 = r * r
        for y in range(y_min, y_max):
            dy = y - cy
            dy2 = dy * dy
            for x in range(x_min, x_max):
                dx = x - cx
                if dx * dx + dy2 <= r2:
                    canvas[y, x, 0] = colors_rgb[i, 0]
                    canvas[y, x, 1] = colors_rgb[i, 1]
                    canvas[y, x, 2] = colors_rgb[i, 2]

        if add_highlights:
            high_r = max(1, int(r * 0.25))
            offset = int(r * 0.35)
            hx = cx - offset
            hy = cy - offset

            hy_min = max(0, hy - high_r)
            hy_max = min(height, hy + high_r + 1)
            hx_min = max(0, hx - high_r)
            hx_max = min(width, hx + high_r + 1)

            high_r2 = high_r * high_r

            for y in range(hy_min, hy_max):
                dy = y - hy
                dy2 = dy * dy
                for x in range(hx_min, hx_max):
                    dx = x - hx
                    if dx * dx + dy2 <= high_r2:
                        canvas[y, x, 0] = 255
                        canvas[y, x, 1] = 255
                        canvas[y, x, 2] = 255

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
        count = random.randint(50, 2000)
        cx, cy = width / 2, height / 2

        x = np.random.uniform(0, width, count)
        y = np.random.uniform(0, height, count)

        dist_x = x - cx
        dist_y = y - cy
        distances = np.sqrt(dist_x**2 + dist_y**2)

        max_dist = max(1, np.sqrt(cx**2 + cy**2))
        norm_dist = distances / max_dist

        base_r = self.max_radius - (self.max_radius - self.min_radius) * norm_dist
        variance_r = np.random.uniform(0.75, 1.25, count)
        final_r = base_r * variance_r

        mode = random.choice(self.all_modes)
        base_hue = random.random()

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

        # Integer centers and radii
        xi = x.astype(np.int32)
        yi = y.astype(np.int32)
        ri = np.maximum(1, final_r.astype(np.int32))

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
        return Image.fromarray(canvas, 'RGB'), count, mode

    def run(self, *args, **kwargs) -> None:
        """
        Multiprocessing generation loop with execution timing.
        """
        with self.timer():
            out_dir = os.path.join(self.config["paths"]["generators_in"], "bubbles")
            os.makedirs(out_dir, exist_ok=True)
            for i in range(self.file_count):
                img, count, mode = self.draw_bubbles(self.width, self.height)
                if img:
                    # Create a unique filename for each image
                    filename = os.path.join(out_dir, f"{self.base_filename}_{i+1}.jpeg")
                    try:
                        # Save the image with the specified filename
                        img.save(filename, quality=95)
                    except Exception as e:
                        self.log.error(f"Failed to save {filename}")

