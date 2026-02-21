import numpy as np
from .rasterTransformer import RasterTransformer

class PosterizationTransformer(RasterTransformer):
    """
    Applies a posterization effect to an image.
    """
    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        np.random.seed()

        t_config = self.config.get("posterizationtransformer", {})

        levels = t_config.get("levels")
        if isinstance(levels, int):
            self.levels = levels 
        else:
            self.levels = 2

        # Ensure that levels is at least 2 for a meaningful effect
        self.levels = max(2, self.levels)
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["levels"] = self.levels
        
        # Create a copy to avoid modifying the original image
        output_np = img_np.copy().astype(np.float32)

        # Calculate the step size for quantizing colors
        step_size = 255.0 / (self.levels - 1)

        # Quantize each color channel
        output_np = np.round(output_np / step_size) * step_size

        return output_np.astype(np.uint8)
