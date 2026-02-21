import numpy as np 
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
