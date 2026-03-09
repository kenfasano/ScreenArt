import numpy as np 
import random
from .rasterTransformer import RasterTransformer

MAX_LIGHT_MOSH_INTENSITY = 0.025  # was 0.004 — 0.4% shift is invisible; 2.5% is visible

class DataMoshTransformer(RasterTransformer):
    """
    Applies a data mosh effect by displacing pixels based on their relationship
    to areas of high change.
    """
    def __init__(self):
        super().__init__() 

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("datamoshtransformer", {})

        # --- Parameter Handling ---
        mosh_intensity = t_config.get("mosh_intensity", "?") 
        if isinstance(mosh_intensity, float):
            self.mosh_intensity = mosh_intensity
        else:
            self.mosh_intensity = random.uniform(0.005, MAX_LIGHT_MOSH_INTENSITY)

        # Clamp the intensity to the valid range [0.0, 1.0]
        self.mosh_intensity = max(0.0, min(1.0, self.mosh_intensity))
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["intensity"] = self.mosh_intensity
        
        height, width = img_np.shape[:2]

        # Generate a grid of coordinates
        y_coords, x_coords = np.indices((height, width))
        
        # Calculate the maximum shift based on intensity
        max_shift_x = int(width * self.mosh_intensity)
        max_shift_y = int(height * self.mosh_intensity)

        # Generate random shifts at reduced resolution and upsample.
        # Shift values are small relative to image size, so per-pixel uniqueness is not visible.
        DOWNSAMPLE = 8
        small_h = max(1, -(-height // DOWNSAMPLE))  # ceiling division
        small_w = max(1, -(-width // DOWNSAMPLE))   # ceiling division
        shift_x = np.repeat(
            np.repeat(np.random.randint(-max_shift_x, max_shift_x + 1, size=(small_h, small_w)), DOWNSAMPLE, axis=0),
            DOWNSAMPLE, axis=1
        )[:height, :width]
        shift_y = np.repeat(
            np.repeat(np.random.randint(-max_shift_y, max_shift_y + 1, size=(small_h, small_w)), DOWNSAMPLE, axis=0),
            DOWNSAMPLE, axis=1
        )[:height, :width]

        # Calculate the new coordinates with wrapping
        new_x = (x_coords + shift_x) % width
        new_y = (y_coords + shift_y) % height

        # Use vectorized indexing to map pixels from their new positions to their old ones
        if img_np.ndim == 3:
            output_np = img_np[new_y, new_x, :]
        else:
            output_np = img_np[new_y, new_x]

        return output_np.astype(np.float32)  # ensure pipeline contract: float32 [0,1]
