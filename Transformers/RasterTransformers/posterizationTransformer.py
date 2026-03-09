import numpy as np
import random
from .rasterTransformer import RasterTransformer

class PosterizationTransformer(RasterTransformer):
    """
    Applies a posterization effect to an image.
    """
    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        np.random.seed()

        t_config = self.config.get("posterizationtransformer", {})

        levels = t_config.get("levels")
        if isinstance(levels, int):
            self.levels = levels
        else:
            self.levels = random.randint(4, 16)

        # Ensure at least 4 for a visible effect (2 = pure B&W)
        self.levels = max(4, self.levels)
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["levels"] = self.levels
        
        # Pipeline contract: float32 [0,1]. Quantize in [0,1] space.
        img_f = np.clip(img_np.astype(np.float32), 0.0, 1.0)
        if img_f.max() > 1.5:  # guard: normalise if somehow [0,255]
            img_f = img_f / 255.0

        step_size = 1.0 / (self.levels - 1)
        output_np = np.round(img_f / step_size) * step_size

        return np.clip(output_np, 0.0, 1.0).astype(np.float32)
