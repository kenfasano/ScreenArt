import cv2
import numpy as np
from .rasterTransformer import RasterTransformer
import random

DEFAULT_SCALE = 1.0
DEFAULT_ITERATIONS = 15

class FractalWarpTransformer(RasterTransformer):
    """
    Applies a fractal warp (kaleidoscope) effect to an image using vectorized operations.
    """

    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("fractalwarptransformer", {})

        # --- Parameter Handling ---
        iterations = t_config.get("iterations")
        if not isinstance(iterations, int):
            iterations = random.randint(8, 20)
        
        scale = t_config.get("scale")
        if scale is None or not isinstance(scale, (int, float)):
            scale = random.uniform(0.5, DEFAULT_SCALE * 1.5)
        
        seed = t_config.get("seed")
        if seed is None:
            seed = np.random.randint(0, 1000000)
        np.random.seed(seed)
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["iter"] = iterations
        self.metadata_dictionary["scale"] = round(scale, 2)
        #self.metadata_dictionary["seed"] = seed
        
        image_type = t_config.get("image_type", "default")
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

        # Pre-compute downsampled noise dimensions once outside the loop.
        # Noise range is ±0.01, so per-pixel uniqueness has no visible benefit.
        _D = 8
        _sh = max(1, -(-height // _D))  # ceiling division
        _sw = max(1, -(-width // _D))   # ceiling division

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
                noise_x = np.repeat(np.repeat(
                    np.random.uniform(-0.01, 0.01, (_sh, _sw)).astype(np.float32), _D, axis=0), _D, axis=1)[:height, :width]
                noise_y = np.repeat(np.repeat(
                    np.random.uniform(-0.01, 0.01, (_sh, _sw)).astype(np.float32), _D, axis=0), _D, axis=1)[:height, :width]
                nx_new += noise_x
                ny_new += noise_y
            
            np.copyto(nx, nx_new, where=active_mask)
            np.copyto(ny, ny_new, where=active_mask)

        map_x = (nx * width + center_x).astype(np.float32)
        map_y = (ny * height + center_y).astype(np.float32)

        img_np = self.to_uint8(img_np)
        try:
            warped = cv2.remap(img_np, map_x, map_y, interpolation=cv2.INTER_LINEAR)
            return self.to_float32(warped)
        except Exception as e:
            # Replaced global log with self.log
            self.log.critical(f"Error during FractalWarp remap: {e}")
            return self.to_float32(img_np)
