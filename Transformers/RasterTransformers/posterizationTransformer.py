import numpy as np # type: ignore
from .base import RasterTransformer

class PosterizationTransformer(RasterTransformer):
    """
    Applies a posterization effect to an image.
    """

    def __init__(self):
        super().__init__()

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        import ScreenArt.common as common
        import ScreenArt.log as log
        """
        Applies the posterization transformation to the input image.
        """
        np.random.seed()

        self.config = common.get_config(config, "posterizationtransformer")

        if self.config is None:
            log.error("config is None for PosterizationTransformer!")
            return img_np 

        levels = common.get_config(self.config, "levels")
        if isinstance(levels, int):
            self.levels = levels 
        else:
            self.levels = 2

        # Ensure that levels is at least 2 for a meaningful effect
        self.levels = max(2, self.levels)
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "levels": self.levels
        }
        # -------------------------
        
        # Create a copy to avoid modifying the original image
        output_np = img_np.copy().astype(np.float32)

        # Calculate the step size for quantizing colors
        step_size = 255.0 / (self.levels - 1)

        # Quantize each color channel
        output_np = np.round(output_np / step_size) * step_size

        return output_np.astype(np.uint8)
