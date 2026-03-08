import numpy as np
import cv2
import random
from .rasterTransformer import RasterTransformer


MAX_ALPHA = 20.0
MAX_SIGMA = 100.0

class FluidWarpTransformer(RasterTransformer):
    def __init__(self):
        super().__init__()

    def _generate_perlin_noise(self, shape: tuple, octaves: int = 1, persistence: float = 0.5) -> np.ndarray:
        noise = (np.random.rand(*shape) * 2 - 1).astype(np.float32)
        ksize = max(1, int(6 * self.sigma + 1)) | 1  # must be odd
        return cv2.GaussianBlur(noise, (ksize, ksize), self.sigma)

    def _create_displacement_map(self, shape: tuple) -> tuple:
        rows, cols = shape
        dx = self._generate_perlin_noise(shape) * self.alpha
        dy = self._generate_perlin_noise(shape) * self.alpha

        x, y = np.meshgrid(np.arange(cols), np.arange(rows))

        indices_x = x + dx
        indices_y = y + dy

        return indices_y, indices_x

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("fluidwarptransformer", {})

        # --- Parameter Handling ---
        self.alpha = t_config.get("alpha")
        if self.alpha is None or not isinstance(self.alpha, (int, float)):
            self.alpha = random.uniform(0.01, MAX_ALPHA)

        sigma = t_config.get("sigma")
        if sigma is None or not isinstance(sigma, (int, float)):
            self.sigma = random.uniform(0.01, MAX_ALPHA)
        else:
            self.sigma = sigma
            
        # --- POPULATE METADATA ---
        self.metadata_dictionary["alpha"] = round(self.alpha, 2)
        self.metadata_dictionary["sigma"] = round(self.sigma, 2)
            
        image_type = t_config.get("image_type", "default")
        
        if image_type == "text":
            interpolation_order = 0  # Nearest Neighbor (crisp)
        else:
            interpolation_order = 1  # Bilinear (blurry)
           
        if img_np.ndim < 2 or img_np.ndim > 3:
           raise ValueError("Input image must be 2D (grayscale) or 3D (color).")

        rows, cols = img_np.shape[:2]
        displacement_map = self._create_displacement_map((rows, cols))

        map_x = displacement_map[1].astype(np.float32)
        map_y = displacement_map[0].astype(np.float32)

        interp = cv2.INTER_NEAREST if interpolation_order == 0 else cv2.INTER_LINEAR

        warped_img = cv2.remap(img_np, map_x, map_y,
                               interpolation=interp,
                               borderMode=cv2.BORDER_REFLECT)

        return warped_img.astype(img_np.dtype)
