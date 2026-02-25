import numpy as np
import cv2
import random

from .rasterTransformer import RasterTransformer

DEFAULT_COUNT = 1
DEFAULT_BRIGHTNESS_THRESHOLD = 95
DEFAULT_STREAK_COLOR = [255, 255, 0]
DEFAULT_STREAK_INTENSITY = 0.5
MAX_BRIGHT_PIXELS = 10000

class AnamorphicTransformer(RasterTransformer):
    """
    Applies an anamorphic lens flare effect using vectorized row accumulation.
    """
    def __init__(self):
        super().__init__()

    def _hex_to_rgb(self, hex_str: str) -> tuple:
        """Helper to replace the external hex_to_rgb dependency."""
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 6:
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        return (255, 255, 255) 

    def get_random_rgb(self) -> tuple:
        """Helper to generate random RGB tuples natively."""
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # FIX: Adopt the new standard run() contract
    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        
        # Access the config directly from the inherited ecosystem
        t_config = self.config.get("anamorphictransformer", {})

        height, width = img_np.shape[:2]

        # --- Parameter Setup ---
        count = t_config.get("count", DEFAULT_COUNT)
        
        # Helper to ensure list
        def to_list(val, length, default):
            if isinstance(val, list):
                return (val * length)[:length]
            return [val] * length

        # Thresholds
        thresh_input = t_config.get("brightness_threshold", DEFAULT_BRIGHTNESS_THRESHOLD)
        thresholds = to_list(thresh_input, count, DEFAULT_BRIGHTNESS_THRESHOLD)

        # Intensities
        intensity_input = t_config.get("streak_intensity", DEFAULT_STREAK_INTENSITY)
        intensities = to_list(intensity_input, count, DEFAULT_STREAK_INTENSITY)

        # --- POPULATE METADATA ---
        self.metadata_dictionary["thresh"] = thresh_input
        self.metadata_dictionary["intensity"] = intensity_input

        # Colors
        colors = t_config.get("streak_colors", None)
        final_colors = []
        
        if colors is None:
            final_colors = [self.get_random_rgb() for _ in range(count)]
        else:
            for c in colors:
                if isinstance(c, str):
                    final_colors.append(self._hex_to_rgb(c))
                else:
                    final_colors.append(c)
            
            # Pad if the config provided too few colors
            while len(final_colors) < count:
                final_colors.append(self.get_random_rgb())
            final_colors = final_colors[:count]
        
        # --- Optimized Processing ---
        if img_np.ndim == 3:
            gray_f32 = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY).astype(np.float32)
        else:
            gray_f32 = img_np.astype(np.float32)

        row_accumulator = np.zeros((height, 3), dtype=np.float32)

        for i in range(count):
            try:
                thresh_val = np.percentile(gray_f32, thresholds[i])
                mask = gray_f32 > thresh_val
                
                num_bright = np.count_nonzero(mask)
                if num_bright == 0:
                    continue
                    
                scaling_factor = 1.0
                if num_bright > MAX_BRIGHT_PIXELS:
                    scaling_factor = MAX_BRIGHT_PIXELS / num_bright

                masked_gray = np.where(mask, gray_f32, 0.0)
                row_sums = np.sum(masked_gray, axis=1) # Shape: (Height,)
                
                base_intensity = (row_sums / 255.0) * scaling_factor * intensities[i]
                streak_contribution = base_intensity[:, np.newaxis] * np.array(final_colors[i])
                
                row_accumulator += streak_contribution

            except Exception as e:
                # FIX: Use the inherited logger
                self.log.error(f"Error in Anamorphic loop {i}: {e}")
                continue

        streak_overlay = row_accumulator[:, np.newaxis, :]
        output_np = np.clip(img_np.astype(np.float32) + streak_overlay, 0, 255).astype(np.uint8)

        return output_np
