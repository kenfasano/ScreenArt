import cv2
import numpy as np 
import random
from .rasterTransformer import RasterTransformer

DEFAULT_SHADOW_HEX = "#FFFF00"
DEFAULT_HILIGHT_HEX = "#0000FF"

class DuotoneTransformer(RasterTransformer):
    """
    Applies a duotone colorization effect to an image.
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
        t_config = self.config.get("duotonetransformer", {})

        shadow_hex = t_config.get("shadow_hex", self.get_random_hex())
        hilight_hex = t_config.get("hilight_hex", self.get_random_hex())
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["shadow"] = shadow_hex
        self.metadata_dictionary["highlight"] = hilight_hex
        
        # Convert hex codes to RGB tuples and store them natively
        self.shadow_rgb = self._hex_to_rgb(shadow_hex)
        self.highlight_rgb = self._hex_to_rgb(hilight_hex)

        if img_np.ndim < 3 or img_np.shape[2] < 3:
            # If grayscale passed in, convert to pseudo-RGB so we can colorize it
            if img_np.ndim == 2:
                img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2RGB)
            else:
                # Use inherited self.log
                self.log.error("Input image must have at least 3 channels (RGB).")
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
