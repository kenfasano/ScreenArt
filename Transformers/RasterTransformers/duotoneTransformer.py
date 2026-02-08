import cv2
import numpy as np # type: ignore
import random
from .base import RasterTransformer

DEFAULT_SHADOW_HEX = "#FFFF00"
DEFAULT_HILIGHT_HEX = "#0000FF"

class DuotoneTransformer(RasterTransformer):
    """
    Applies a duotone colorization effect to an image.
    """

    def __init__(self):
        super().__init__()

    def get_random_hex(self):
        return '#{:06x}'.format(random.randint(0, 0xFFFFFF))

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        from Transformers import hex_to_rgb
        import common
        import log
        
        # Corrected config key from 'radialwarptransformer' to 'duotonetransformer'
        self.config = common.get_config(config, "duotonetransformer")

        shadow_hex = self.get_random_hex() # self.config.get("shadow_hex", DEFAULT_SHADOW_HEX)
        hilight_hex = self.get_random_hex() # self.config.get("hilight_hex", DEFAULT_HILIGHT_HEX)
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "shadow": shadow_hex,
            "highlight": hilight_hex
        }
        # -------------------------
        
        # Convert hex codes to RGB tuples and store them
        self.shadow_rgb = hex_to_rgb.convert(shadow_hex)
        self.highlight_rgb = hex_to_rgb.convert(hilight_hex)

        if img_np.ndim < 3 or img_np.shape[2] < 3:
            # If grayscale passed in, convert to pseudo-RGB so we can colorize it
            if img_np.ndim == 2:
                img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2RGB)
            else:
                log.error("Input image must have at least 3 channels (RGB).")
                return img_np

        # Step 1: Convert to grayscale (luminosity method)
        grayscale_np = np.dot(img_np[...,:3], [0.299, 0.587, 0.114]).astype(np.uint8)

        # Step 2: Create an empty output array
        output_np = np.zeros_like(img_np)

        # Step 3: Map grayscale intensity to duotone gradient
        shadow_np = np.array(self.shadow_rgb, dtype=np.float32)
        highlight_np = np.array(self.highlight_rgb, dtype=np.float32)

        # Normalize grayscale values to 0-1
        normalized_grayscale = grayscale_np.astype(np.float32) / 255.0

        # Perform the linear interpolation for each color channel
        for i in range(3):
            output_np[..., i] = (shadow_np[i] * (1 - normalized_grayscale) +
                                  highlight_np[i] * normalized_grayscale)

        return output_np.astype(np.uint8)
