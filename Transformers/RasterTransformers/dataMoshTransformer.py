import numpy as np # type: ignore
import random
from .base import RasterTransformer

MAX_LIGHT_MOSH_INTENSITY = 0.004

class DataMoshTransformer(RasterTransformer):
    """
    Applies a data mosh effect by displacing pixels based on their relationship
    to areas of high change.
    """

    def __init__(self):
        super().__init__() 

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        import common
        import log
        """
        Applies the data mosh transformation to the input image using vectorized operations.
        """

        self.config = common.get_config(config, "datamoshtransformer")

        # --- Parameter Handling ---
        mosh_intensity = self.config.get("mosh_intensity", "?") 
        if isinstance(mosh_intensity, float):
            self.mosh_intensity = mosh_intensity
        else:
            self.mosh_intensity = random.uniform(0.01, MAX_LIGHT_MOSH_INTENSITY)

        # Clamp the intensity to the valid range [0.0, 1.0]
        self.mosh_intensity = max(0.0, min(1.0, self.mosh_intensity))
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "intensity": self.mosh_intensity
        }
        # -------------------------
        
        height, width = img_np.shape[:2]

        # Generate a grid of coordinates
        y_coords, x_coords = np.indices((height, width))
        
        # Calculate the maximum shift based on intensity
        max_shift_x = int(width * self.mosh_intensity)
        max_shift_y = int(height * self.mosh_intensity)

        # Generate random shifts for each pixel, vectorized
        shift_x = np.random.randint(-max_shift_x, max_shift_x + 1, size=(height, width))
        shift_y = np.random.randint(-max_shift_y, max_shift_y + 1, size=(height, width))

        # Calculate the new coordinates with wrapping
        new_x = (x_coords + shift_x) % width
        new_y = (y_coords + shift_y) % height

        # Use vectorized indexing to map pixels from their new positions to their old ones
        # Handle 2D (grayscale) or 3D (color) arrays
        if img_np.ndim == 3:
            output_np = img_np[new_y, new_x, :]
        else:
            output_np = img_np[new_y, new_x]

        return output_np.astype(np.uint8)
