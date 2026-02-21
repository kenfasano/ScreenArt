import cv2 
import numpy as np 
import random
from typing import Optional, TypeAlias
from .rasterTransformer import RasterTransformer

OptionalInt: TypeAlias = Optional[int] 
DEFAULT_COUNT = 1
DEFAULT_STYLE = "push"
DEFAULT_STRENGTH = 70.0
DEFAULT_RADIUS = 0.05 

class RadialWarpTransformer(RasterTransformer):
    """
    Applies localized radial push/pull warps to the image.
    """
    def __init__(self):
        super().__init__()
        self.allowed_styles = ["push", "pull"]

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("radialwarptransformer", {})

        height, width = img_np.shape[:2]

        # --- Parameter Handling ---
        count = t_config.get("count", "?")
        if not isinstance(count, int):
            count = int(random.uniform(DEFAULT_COUNT // 2, DEFAULT_COUNT * 2))

        style = t_config.get("style", "?")
        if isinstance(style, str):
            if style == "?": 
                style = [random.choice(self.allowed_styles) for _ in range(count)]
            else: 
                style = [style]
        elif not isinstance(style, list): 
            style = [style]

        strength = t_config.get("strength", "?")
        if isinstance(strength, str):
            strength = [random.uniform(DEFAULT_STRENGTH // 2, DEFAULT_STRENGTH * 2) for _ in range(count)]
        elif not isinstance(strength, list):
            strength = [strength]
            
        center_x = t_config.get("center_x", "?")
        if isinstance(center_x, list):
            center_x = [float(v) for v in center_x]
        elif center_x is None or center_x == "?":
            center_x = [random.uniform(0.0, 1.0) for _ in range(count)]
        else: 
            center_x = [float(center_x)]

        center_y = t_config.get("center_y", "?")
        if isinstance(center_y, list):
            center_y = [float(v) for v in center_y]
        elif center_y is None or center_y == "?":
            center_y = [random.uniform(0.0, 1.0) for _ in range(count)]
        else: 
            center_y = [float(center_y)]

        radius = t_config.get("radius", "?")
        if isinstance(radius, list):
            radius = [float(v) for v in radius]
        elif radius is None or radius == "?":
            radius = [random.uniform(DEFAULT_RADIUS * 0.5, DEFAULT_RADIUS * 2.0) for _ in range(count)]
        else: 
            radius = [float(radius)]

        # --- POPULATE METADATA ---
        self.metadata_dictionary["style"] = style
        self.metadata_dictionary["strength"] = strength
        self.metadata_dictionary["radius"] = radius

        # Extend lists
        strength = (strength * count)[:count]
        center_x = (center_x * count)[:count]
        center_y = (center_y * count)[:count]
        radius = (radius * count)[:count]
        style = (style * count)[:count]

        # Convert to pixels
        try:
            px_center_x = np.clip([v * width for v in center_x], 0, width - 1).astype(int)
            px_center_y = np.clip([v * height for v in center_y], 0, height - 1).astype(int)
            px_radius = np.clip([v * min(height, width) for v in radius], 1, min(height, width)).astype(int)
        except Exception as e:
            self.log.error(f"Could not convert coordinate percentages: {e}")
            return img_np 

        # --- OPTIMIZED WARP LOGIC ---
        map_x, map_y = np.meshgrid(np.arange(width, dtype=np.float32), 
                                   np.arange(height, dtype=np.float32))

        for i in range(count):
            cx, cy, r = px_center_x[i], px_center_y[i], px_radius[i]
            s = strength[i]
            direction = 1.0 if style[i] == 'push' else -1.0

            x1, x2 = max(0, cx - r), min(width, cx + r + 1)
            y1, y2 = max(0, cy - r), min(height, cy + r + 1)
            
            if x1 >= x2 or y1 >= y2:
                continue

            roi_map_x = map_x[y1:y2, x1:x2]
            roi_map_y = map_y[y1:y2, x1:x2]

            dx = roi_map_x - cx
            dy = roi_map_y - cy
            
            dist_sq = dx*dx + dy*dy
            r_sq = r * r
            
            mask = dist_sq < r_sq
            
            if not np.any(mask):
                continue

            dist = np.sqrt(dist_sq[mask])
            dist[dist == 0] = 1.0 
            
            warp_effect = s * np.exp(-dist / (r / 3.0))
            shift = direction * warp_effect
            
            roi_map_x[mask] += (dx[mask] / dist) * shift
            roi_map_y[mask] += (dy[mask] / dist) * shift

        try:
            warped = cv2.remap(img_np, map_x, map_y, interpolation=cv2.INTER_LINEAR)
            return warped
        except Exception as e:
            self.log.critical(f"Error during final remap: {e}")
            return img_np
