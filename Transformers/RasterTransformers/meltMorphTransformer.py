import numpy as np
from .rasterTransformer import RasterTransformer

DEFAULT_MELT_INTENSITY = 0.5

class MeltMorphTransformer(RasterTransformer):
    """
    Applies a melt effect to an image, reminiscent of Salvador Dali's artwork.
    Uses vectorized operations to morph the input image.
    """
    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        np.random.seed()
        
        # Convert to grayscale to determine luminosity
        grayscale_np = np.dot(img_np[...,:3], [0.299, 0.587, 0.114]).astype(np.float32)

        height, width, _ = img_np.shape

        t_config = self.config.get("meltmorphtransformer", {})

        # --- Parameter Handling ---
        self.melt_intensity = t_config.get("melt_intensity")
        if not isinstance(self.melt_intensity, (int, float)):
            self.melt_intensity = DEFAULT_MELT_INTENSITY

        # Clamp the intensity to the valid range [0, 1]
        self.melt_intensity = max(0.0, min(1.0, self.melt_intensity))
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["intensity"] = round(self.melt_intensity, 2)
        
        # Calculate the melt shift for all pixels at once based on luminosity
        shifts = (self.melt_intensity * (1 - grayscale_np / 255.0) * height * 0.1).astype(int)

        # Generate a random vertical offset for all pixels
        random_offset = np.random.randint(-5, 6, size=(height, width))

        # Create coordinate arrays for vectorized indexing
        y_coords, x_coords = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')

        # Calculate the new y-coordinates for all pixels
        new_y_coords = np.clip(y_coords - shifts + random_offset, 0, height - 1)
        
        # Use advanced indexing to create the final warped image
        output_np = img_np[new_y_coords, x_coords]

        return output_np.astype(np.uint8)
