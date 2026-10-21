import numpy as np
import random
from .rasterTransformer import RasterTransformer

class InvertRGBTransformer(RasterTransformer):
    """
    Inverts the colors of an RGB image, blended with the original to preserve structure.
    """
    def __init__(self):
        super().__init__()
        
    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("invertrgbtransformer", {})
        blend = t_config.get("blend")
        if not isinstance(blend, (int, float)):
            blend = random.uniform(0.4, 0.85)
        blend = max(0.0, min(1.0, float(blend)))
        self.metadata_dictionary["blend"] = round(blend, 2)
        # Pipeline contract: float32 [0,1] in, [0,1] out.
        # Inversion in [0,1] space: inverted = 1.0 - img
        img_f = img_np.astype(np.float32)
        if img_f.max() > 1.5:  # guard: already uint8-range float, normalise
            img_f = img_f / 255.0
        inverted = 1.0 - img_f
        return np.clip(inverted * blend + img_f * (1.0 - blend), 0.0, 1.0).astype(np.float32)
