import os
import numpy as np
from numba import njit
import random
from PIL import Image
from numpy.typing import NDArray
from typing import Callable, Tuple
from .drawGenerator import DrawGenerator

HSVArrays = Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]
ModeFunc = Callable[
    [float, NDArray[np.float32], NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]],
    HSVArrays,
]


@njit(fastmath=True, cache=True)
def _draw_bubbles_jit(
    canvas,         # (H, W, 3) uint8, already has background
    xi, yi, ri,
    colors_rgb,     # (N, 3) float32  body colour [0,1]
    light_x,        # float – light source position (canvas coords)
    light_y,
):
    """
    Render each bubble as a shaded glass sphere:

    For every pixel (px, py) inside radius r centred at (cx, cy):

      1. Compute normalised surface normal  n = (dx/r, dy/r, nz)
         where nz = sqrt(1 - dx²/r² - dy²/r²)

      2. Limb darkening:  base colour × nz^0.6
         → edges fade toward dark/transparent

      3. Fresnel-ish rim: near the edge (nz < 0.35) add a bright
         cyan-white tint  → gives the glass refraction ring

      4. Specular highlight: Blinn-Phong.  Light direction L is
         normalised (light_x - cx, light_y - cy, dist_to_light).
         Halfway vector H = normalize(L + V) where V = (0,0,1).
         spec = max(0, dot(N, H))^60  scaled to white flash.

      5. Alpha compositing over the existing canvas pixel:
         alpha = nz^1.2  (centre opaque → edge transparent)
    """
    height = canvas.shape[0]
    width  = canvas.shape[1]
    count  = xi.shape[0]

    for i in range(count):
        cx = xi[i]
        cy = yi[i]
        r  = ri[i]
        if r < 1:
            continue

        r_f = float(r)
        r2  = r_f * r_f

        # Body colour
        br = colors_rgb[i, 0]
        bg = colors_rgb[i, 1]
        bb = colors_rgb[i, 2]

        # Light direction (3D) – light is above the canvas plane
        ldx = float(light_x - cx)
        ldy = float(light_y - cy)
        ldz = r_f * 3.0          # "above" the sphere
        l_len = (ldx*ldx + ldy*ldy + ldz*ldz) ** 0.5
        if l_len < 1e-6:
            l_len = 1e-6
        lx = ldx / l_len
        ly = ldy / l_len
        lz = ldz / l_len

        y_min = max(0,      cy - r)
        y_max = min(height, cy + r + 1)
        x_min = max(0,      cx - r)
        x_max = min(width,  cx + r + 1)

        for py in range(y_min, y_max):
            dy   = float(py - cy)
            dy2  = dy * dy

            for px in range(x_min, x_max):
                dx  = float(px - cx)
                d2  = dx*dx + dy2
                if d2 > r2:
                    continue

                # --- Surface normal ---
                nx_ = dx / r_f
                ny_ = dy / r_f
                nz_ = (1.0 - nx_*nx_ - ny_*ny_)
                if nz_ < 0.0:
                    nz_ = 0.0
                nz_ = nz_ ** 0.5

                # --- Diffuse (Lambert) ---
                diff = nx_*lx + ny_*ly + nz_*lz
                if diff < 0.0:
                    diff = 0.0

                # --- Specular (Blinn-Phong) ---
                # View direction V = (0,0,1)
                hx_ = lx
                hy_ = ly
                hz_ = lz + 1.0
                h_len = (hx_*hx_ + hy_*hy_ + hz_*hz_) ** 0.5
                if h_len > 1e-6:
                    hx_ /= h_len; hy_ /= h_len; hz_ /= h_len
                spec_dot = nx_*hx_ + ny_*hy_ + nz_*hz_
                if spec_dot < 0.0:
                    spec_dot = 0.0
                spec = spec_dot ** 60

                # --- Limb darkening ---
                limb = nz_ ** 0.6

                # --- Fresnel rim (glass edge glow) ---
                rim = 0.0
                if nz_ < 0.35:
                    rim = (0.35 - nz_) / 0.35   # 0→1 at very edge

                # --- Alpha (glass transparency at edges) ---
                alpha = nz_ ** 1.2
                if alpha > 1.0:
                    alpha = 1.0

                # --- Compose colour ---
                shade = diff * 0.6 + 0.4        # ambient 0.4 + diffuse
                cr = br * shade * limb
                cg = bg * shade * limb
                cb = bb * shade * limb

                # Rim: cyan-white tint
                cr = cr + rim * 0.55
                cg = cg + rim * 0.75
                cb = cb + rim * 0.85

                # Specular: white flash
                cr = cr + spec * 0.95
                cg = cg + spec * 0.95
                cb = cb + spec * 0.95

                if cr > 1.0: cr = 1.0
                if cg > 1.0: cg = 1.0
                if cb > 1.0: cb = 1.0

                # --- Alpha composite over canvas ---
                bg_r = float(canvas[py, px, 0]) / 255.0
                bg_g = float(canvas[py, px, 1]) / 255.0
                bg_b = float(canvas[py, px, 2]) / 255.0

                out_r = cr * alpha + bg_r * (1.0 - alpha)
                out_g = cg * alpha + bg_g * (1.0 - alpha)
                out_b = cb * alpha + bg_b * (1.0 - alpha)

                canvas[py, px, 0] = int(out_r * 255.0)
                canvas[py, px, 1] = int(out_g * 255.0)
                canvas[py, px, 2] = int(out_b * 255.0)


class Bubbles(DrawGenerator):
    def __init__(self):
        super().__init__()

        self.width      = int(self.config.get('width',  1920))
        self.height     = int(self.config.get('height', 1080))
        self.file_count = 10
        self.min_radius = int(self.config.get('min_radius', 10))
        self.max_radius = int(self.config.get('max_radius', 60))
        self.base_filename = "bubbles"

        self.mode_map: dict[str, ModeFunc] = {
            "radial_flip":    self._mode_radial_flip,
            "radial_rainbow": self._mode_radial_rainbow,
            "fire":           self._mode_fire,
            "cool":           self._mode_cool,
            "pastel":         self._mode_pastel,
            "monochrome":     self._mode_monochrome,
        }
        self.all_modes = list(self.mode_map.keys())

    # ------------------------------------------------------------------
    # Colour modes  (unchanged contract: return h, s, v float32 arrays)
    # ------------------------------------------------------------------

    def _hsv_to_rgb_vectorized(self, h, s, v) -> NDArray[np.float32]:
        h = h % 1.0
        i = (h * 6.0).astype(int)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        cond = [i==0, i==1, i==2, i==3, i==4, i==5]
        r = np.select(cond, [v, q, p, p, t, v])
        g = np.select(cond, [t, v, v, q, p, p])
        b = np.select(cond, [p, p, t, v, v, q])
        return np.stack((r, g, b), axis=-1).astype(np.float32)

    def _mode_radial_flip(self, base_hue, norm_dist, jitters, s_r, v_r):
        h = (base_hue + norm_dist * 0.5) % 1.0
        s = np.clip(0.75 + s_r, 0, 1)
        v = np.clip(0.85 + v_r, 0, 1)
        return h, s, v

    def _mode_radial_rainbow(self, base_hue, norm_dist, jitters, s_r, v_r):
        h = (base_hue + norm_dist) % 1.0
        s = np.clip(0.80 + s_r, 0, 1)
        v = np.clip(0.90 + v_r, 0, 1)
        return h, s, v

    def _mode_fire(self, base_hue, norm_dist, jitters, s_r, v_r):
        h = np.minimum(0.12, np.abs(jitters) * 1.5)
        s = np.clip(0.85 + np.abs(s_r), 0, 1)
        v = np.clip(0.80 + np.abs(v_r), 0, 1)
        return h, s, v

    def _mode_cool(self, base_hue, norm_dist, jitters, s_r, v_r):
        h = np.clip(0.50 + jitters * 0.4, 0.45, 0.75)
        s = np.clip(0.70 + s_r, 0, 1)
        v = np.clip(0.80 + v_r, 0, 1)
        return h, s, v

    def _mode_pastel(self, base_hue, norm_dist, jitters, s_r, v_r):
        h = (base_hue + jitters * 2.0) % 1.0
        s = np.clip(0.35 + np.abs(s_r), 0, 0.6)
        v = np.clip(0.88 + v_r * 0.5,  0, 1)
        return h, s, v

    def _mode_monochrome(self, base_hue, norm_dist, jitters, s_r, v_r):
        h = np.full_like(norm_dist, base_hue)
        s = np.clip(0.80 + s_r, 0, 1)
        v = np.clip(0.30 + norm_dist * 0.65 + v_r * 0.1, 0, 1)
        return h, s, v

    # ------------------------------------------------------------------
    # Main draw
    # ------------------------------------------------------------------

    def draw_bubbles(self, width: int, height: int) -> Image.Image:
        cx_canvas = width  / 2.0
        cy_canvas = height / 2.0
        max_dist  = max(1, np.sqrt(cx_canvas**2 + cy_canvas**2))

        # Random light source: anywhere in the upper hemisphere of the canvas
        light_x = float(random.uniform(width  * 0.1, width  * 0.9))
        light_y = float(random.uniform(height * 0.05, height * 0.5))

        # --- Area budget ---
        target_pixels = width * height * random.uniform(0.4, 0.7)
        xs, ys, rs = [], [], []
        total_area = 0.0

        while total_area < target_pixels:
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            dx = x - cx_canvas
            dy = y - cy_canvas
            nd = np.sqrt(dx*dx + dy*dy) / max_dist
            eff_max = self.max_radius * 0.9
            base_r  = eff_max - (eff_max - self.min_radius) * nd
            variance = random.random() ** 2 * 0.5 + 0.75
            r = int(max(1, base_r * variance))
            xs.append(int(x)); ys.append(int(y)); rs.append(r)
            total_area += np.pi * r * r

        count = len(rs)
        xi = np.array(xs, dtype=np.int32)
        yi = np.array(ys, dtype=np.int32)
        ri = np.array(rs, dtype=np.int32)

        # --- Colour ---
        mode     = random.choice(self.all_modes)
        base_hue = random.random()
        dx_a = xi.astype(np.float32) - cx_canvas
        dy_a = yi.astype(np.float32) - cy_canvas
        norm_dist = np.sqrt(dx_a**2 + dy_a**2) / max_dist
        jitters = np.random.uniform(-0.05, 0.05, count).astype(np.float32)
        s_r     = np.random.uniform(-0.10, 0.10, count).astype(np.float32)
        v_r     = np.random.uniform(-0.10, 0.10, count).astype(np.float32)

        h, s, v = self.mode_map[mode](base_hue, norm_dist, jitters, s_r, v_r)
        s = np.clip(s, 0.0, 1.0).astype(np.float32)
        v = np.clip(v, 0.0, 1.0).astype(np.float32)

        # float32 [0,1] colours for the JIT kernel
        colors_f32 = self._hsv_to_rgb_vectorized(h, s, v)  # (N,3) float32

        # --- Paint small before large so big bubbles occlude small ---
        order      = np.argsort(ri)
        xi         = xi[order]
        yi         = yi[order]
        ri         = ri[order]
        colors_f32 = colors_f32[order]

        # --- Dark background so glass effect reads clearly ---
        bg_value = random.randint(5, 25)
        canvas   = np.full((height, width, 3), bg_value, dtype=np.uint8)

        _draw_bubbles_jit(canvas, xi, yi, ri, colors_f32, light_x, light_y)

        return Image.fromarray(canvas, 'RGB')

    def run(self, *args, **kwargs) -> None:
        out_dir = os.path.join(self.config["paths"]["generators_in"], "bubbles")
        os.makedirs(out_dir, exist_ok=True)
        for i in range(self.file_count):
            img = self.draw_bubbles(self.width, self.height)
            filename = os.path.join(out_dir, f"{self.base_filename}_{i+1}.jpeg")
            img.save(filename, quality=95)
