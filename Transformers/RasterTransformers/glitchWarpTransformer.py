import numpy as np
import random
from .rasterTransformer import RasterTransformer

class GlitchWarpTransformer(RasterTransformer):
    """
    Applies a glitch warp effect to an image by randomly shifting horizontal rows
    of pixels.
    """
    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("glitchwarptransformer", {})

        self.warp_intensity = t_config.get("warp_intensity")
        if not isinstance(self.warp_intensity, (int, float)):
            self.warp_intensity = random.uniform(0.0, 1.0)

        # Clamp the intensity to the valid range [0, 1]
        self.warp_intensity = max(0.0, min(1.0, self.warp_intensity))
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["intensity"] = round(self.warp_intensity, 2)

        # Set the random seed for reproducible glitches
        seed = random.randint(0, 1000000)
        np.random.seed(seed)
        height, width, _ = img_np.shape

        max_shift = int(width * self.warp_intensity)
        shifts = np.random.randint(-max_shift, max_shift + 1, size=height)

        x_indices = np.arange(width)
        
        # Broadcasting shift
        new_x_indices = (x_indices - shifts[:, np.newaxis]) % width

        # Advanced indexing
        output_np = img_np[np.arange(height)[:, np.newaxis], new_x_indices]

        return output_np.astype(np.uint8)
