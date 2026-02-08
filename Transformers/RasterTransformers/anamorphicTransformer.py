import numpy as np # type: ignore
import cv2 # type: ignore
import random
from .base import RasterTransformer

# MOVED IMPORTS INSIDE METHODS TO BREAK CIRCULAR LOOP

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

    def get_random_hex(self):
        import hex_to_rgb
        return hex_to_rgb.convert("{:06x}".format(random.randint(0, 0xFFFFFF)))

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        from Transformers import hex_to_rgb
        import common
        import log
        # LAZY IMPORTS: Prevent circular dependency
        
        self.config = common.get_config(config, "anamorphictransformer")

        height, width = img_np.shape[:2]

        # --- Parameter Setup ---
        count = self.config.get("count", DEFAULT_COUNT)

        # --- Random Generation (Ignoring Config) ---
        
        # Thresholds: Random percentile between 90.0 and 99.9
        # (Higher means only the very brightest pixels trigger streaks)
        thresholds = [random.uniform(90.0, 99.9) for _ in range(count)]

        # Intensities: Random multiplier between 0.3 and 0.8
        intensities = [random.uniform(0.3, 0.8) for _ in range(count)]

        # Colors: Random RGB values
        final_colors = [[random.randint(0, 255) for _ in range(3)] for _ in range(count)]

        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "thresh": thresholds,
            "intensity": intensities,
            "colors": final_colors
        }
        
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
                log.error(f"Error in Anamorphic loop {i}: {e}")
                continue

        streak_overlay = row_accumulator[:, np.newaxis, :]
        output_np = np.clip(img_np.astype(np.float32) + streak_overlay, 0, 255).astype(np.uint8)

        return output_np

