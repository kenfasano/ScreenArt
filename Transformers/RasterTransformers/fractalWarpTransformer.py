import cv2 # type: ignore
import numpy as np # type: ignore
from .base import RasterTransformer
import random

DEFAULT_SCALE = 1.0
DEFAULT_ITERATIONS = 15

class FractalWarpTransformer(RasterTransformer):
    """
    Applies a fractal warp (kaleidoscope) effect to an image using vectorized operations.
    """

    def __init__(self):
        super().__init__()

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        import ScreenArt.log as log
        import ScreenArt.common as common

        self.config = common.get_config(config, "fractalwarptransformer")

        # --- Parameter Handling ---
        iterations = self.config.get("iterations", DEFAULT_ITERATIONS)
        if not isinstance(iterations, int):
             iterations = DEFAULT_ITERATIONS
        
        scale = self.config.get("scale", None)
        if scale is None or not isinstance(scale, (int, float)):
            scale = random.uniform(0.5, DEFAULT_SCALE * 1.5)
        
        seed = self.config.get("seed", None)
        if seed is None:
            seed = np.random.randint(0, 1000000)
        np.random.seed(seed)
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "iter": iterations,
            "scale": scale,
            "seed": seed
        }
        # -------------------------
        
        image_type = self.config.get("image_type", "default")
        apply_noise = (image_type != "text")

        height, width = img_np.shape[:2]

        # --- VECTORIZED LOGIC ---
        map_x, map_y = np.meshgrid(np.arange(width, dtype=np.float32),
                                   np.arange(height, dtype=np.float32))

        center_x = width / 2.0
        center_y = height / 2.0
        
        nx = (map_x - center_x) / width
        ny = (map_y - center_y) / height

        active_mask = np.ones((height, width), dtype=bool)

        for _ in range(iterations):
            r_sq = nx * nx + ny * ny
            escaped_now = r_sq > 4
            active_mask = active_mask & (~escaped_now)
            
            if not np.any(active_mask):
                break

            angle = np.arctan2(ny, nx)
            r = np.sqrt(r_sq)

            nx_new = r * np.cos(scale * angle)
            ny_new = r * np.sin(scale * angle)

            if apply_noise:
                noise_x = np.random.uniform(-0.01, 0.01, (height, width)).astype(np.float32)
                noise_y = np.random.uniform(-0.01, 0.01, (height, width)).astype(np.float32)
                nx_new += noise_x
                ny_new += noise_y
            
            np.copyto(nx, nx_new, where=active_mask)
            np.copyto(ny, ny_new, where=active_mask)

        map_x = (nx * width + center_x).astype(np.float32)
        map_y = (ny * height + center_y).astype(np.float32)

        try:
            warped = cv2.remap(img_np, map_x, map_y, interpolation=cv2.INTER_LINEAR)
            return warped
        except Exception as e:
            log.critical(f"Error during FractalWarp remap: {e}")
            return img_np
