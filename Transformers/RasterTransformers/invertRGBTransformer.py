import numpy as np
from .rasterTransformer import RasterTransformer

class InvertRGBTransformer(RasterTransformer):
    """
    Inverts the colors of an RGB image.
    """
    def __init__(self):
        super().__init__()
        
    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        self.metadata_dictionary["invert"] = True
        return 255 - img_np
