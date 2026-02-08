from .base import RasterTransformer # Relative import
import numpy as np # type: ignore

class NullTransformer(RasterTransformer):
    def __init__(self):
        super().__init__()

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        return img_np 

