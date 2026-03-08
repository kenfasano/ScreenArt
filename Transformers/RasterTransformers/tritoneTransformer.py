import numpy as np 
import cv2
import random
from .rasterTransformer import RasterTransformer

class TritoneTransformer(RasterTransformer):
    """
    Applies a tritone colorization effect to an image.
    """
    def __init__(self):
        super().__init__()

    def get_random_hex(self) -> str:
        return '#{:06x}'.format(random.randint(0, 0xFFFFFF))

    def _hex_to_rgb(self, hex_str: str) -> tuple:
        """Helper to replace the external hex_to_rgb dependency."""
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 6:
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        return (255, 255, 255) 

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("tritonetransformer", {})

        shadow_hex = t_config.get("shadow_hex", self.get_random_hex())
        mid_hex = t_config.get("mid_hex", self.get_random_hex())
        hilight_hex = t_config.get("hilight_hex", self.get_random_hex())
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["shadow"] = shadow_hex
        self.metadata_dictionary["mid"] = mid_hex
        self.metadata_dictionary["highlight"] = hilight_hex

        # Convert hex codes to RGB tuples natively
        self.shadow_rgb = self._hex_to_rgb(shadow_hex)
        self.mid_rgb = self._hex_to_rgb(mid_hex)
        self.highlight_rgb = self._hex_to_rgb(hilight_hex)

        if img_np.ndim < 3 or img_np.shape[2] < 3:
            raise ValueError("Input image must have at least 3 channels (RGB).")

        shadow_np    = np.array(self.shadow_rgb,    dtype=np.float32)
        mid_np       = np.array(self.mid_rgb,       dtype=np.float32)
        highlight_np = np.array(self.highlight_rgb, dtype=np.float32)

        # Build a 256-entry RGB LUT: shadow->mid for dark half, mid->highlight for light half.
        # Cost: ~0.04ms. Avoids expensive per-pixel np.where across full-image arrays.
        idx = np.arange(256, dtype=np.float32)
        t = idx / 255.0
        dark = t <= 0.5
        t2_dark  = (t * 2.0)[:, np.newaxis]
        t2_light = ((t - 0.5) * 2.0)[:, np.newaxis]
        lut = np.empty((256, 3), dtype=np.float32)
        lut[dark]  = shadow_np * (1 - t2_dark[dark])  + mid_np       * t2_dark[dark]
        lut[~dark] = mid_np    * (1 - t2_light[~dark]) + highlight_np * t2_light[~dark]

        # Convert to grayscale and apply LUT via fancy indexing
        gray = cv2.cvtColor(self.to_uint8(img_np), cv2.COLOR_RGB2GRAY)
        return np.clip(lut[gray], 0, 255)
