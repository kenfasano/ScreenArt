import numpy as np # type: ignore
from .base import RasterTransformer

class InvertRGBTransformer(RasterTransformer):
    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        # Invert the image by subtracting the pixel values from 255.
        inverted_img_np = 255 - img_np
        return inverted_img_np

