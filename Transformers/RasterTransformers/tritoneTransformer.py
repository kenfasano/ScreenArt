import numpy as np # type: ignore
import random
from .base import RasterTransformer

DEFAULT_SHADOW_HEX = "#FFFF00"
DEFAULT_MID_HEX = "#999999"
DEFAULT_HILIGHT_HEX = "#0000FF"

class TritoneTransformer(RasterTransformer):
    """
    Applies a tritone colorization effect to an image.
    """

    def __init__(self):
        super().__init__()

    # Helper function to generate a random hex color
    def get_random_hex(self):
        # ABSOLUTE IMPORT (Safe)
        return '#{:06x}'.format(random.randint(0, 0xFFFFFF))

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        from Transformers import hex_to_rgb
        import common
        import log
        
        # Corrected config key
        self.config = common.get_config(config, "tritonetransformer")

        if self.config is None:
            log.error("config is None for TritoneTransformer!")
            return img_np 

        shadow_hex = self.get_random_hex() #self.config.get("shadow_hex", DEFAULT_SHADOW_HEX)
        mid_hex = self.get_random_hex() #self.config.get("mid_hex", DEFAULT_MID_HEX)
        hilight_hex = self.get_random_hex() #self.config.get("hilight_hex", DEFAULT_HILIGHT_HEX)
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "shadow": shadow_hex,
            "mid": mid_hex,
            "highlight": hilight_hex
        }
        # -------------------------

        # Convert hex codes to RGB tuples and store them
        self.shadow_rgb = hex_to_rgb.convert(shadow_hex)
        self.mid_rgb = hex_to_rgb.convert(mid_hex)
        self.highlight_rgb = hex_to_rgb.convert(hilight_hex)

        if img_np.ndim < 3 or img_np.shape[2] < 3:
            raise ValueError("Input image must have at least 3 channels (RGB).")

        # Step 1: Convert to grayscale
        grayscale_np = np.dot(img_np[...,:3], [0.299, 0.587, 0.114]).astype(np.float32)

        # Normalize grayscale values to the 0-1 range for interpolation
        normalized_grayscale = grayscale_np / 255.0

        # Create numpy arrays for the RGB colors
        shadow_np = np.array(self.shadow_rgb, dtype=np.float32)
        mid_np = np.array(self.mid_rgb, dtype=np.float32)
        highlight_np = np.array(self.highlight_rgb, dtype=np.float32)
        
        # Determine the output color based on pixel intensity
        output_np = np.zeros_like(img_np, dtype=np.float32)

        # Interpolate for the darker half (0-0.5 normalized grayscale)
        dark_mask = normalized_grayscale <= 0.5
        dark_normalized = np.where(dark_mask, normalized_grayscale / 0.5, 0)
        
        # Interpolate for the lighter half (0.5-1.0 normalized grayscale)
        light_mask = normalized_grayscale > 0.5
        light_normalized = np.where(light_mask, (normalized_grayscale - 0.5) / 0.5, 0)

        for i in range(3):
            output_np[..., i] = np.where(
                dark_mask,
                (mid_np[i] * dark_normalized) + (shadow_np[i] * (1 - dark_normalized)),
                (highlight_np[i] * light_normalized) + (mid_np[i] * (1 - light_normalized))
            )
            
        return np.clip(output_np, 0, 255).astype(np.uint8)
