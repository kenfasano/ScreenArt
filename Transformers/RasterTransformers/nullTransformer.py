import numpy as np
from .rasterTransformer import RasterTransformer

class NullTransformer(RasterTransformer):
    """
    A pass-through transformer that does nothing. Useful for testing or disabling slots.
    """
    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        self.metadata_dictionary["null"] = True
        return img_np
