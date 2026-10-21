import numpy as np
import cv2
import random
from .rasterTransformer import RasterTransformer


class OilPaintingTransformer(RasterTransformer):
    """
    Applies an oil painting effect using cv2.xphoto.oilPainting().
    Produces a painterly texture distinct from WatercolorTransformer —
    stronger colour saturation, harder brush strokes, more vivid output.
    """

    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("oilpaintingtransformer", {})

        # Brush size (neighbourhood radius): 1-9, odd preferred
        size = t_config.get("size")
        if not isinstance(size, int):
            size = random.choice([3, 4, 5, 6, 7, 8])

        # Histogram bins: higher = more colour detail preserved
        dyn_ratio = t_config.get("dyn_ratio")
        if not isinstance(dyn_ratio, int):
            dyn_ratio = random.randint(1, 8)

        self.metadata_dictionary["size"]      = size
        self.metadata_dictionary["dyn_ratio"] = dyn_ratio

        img = self.to_uint8(img_np)

        # cv2.xphoto.oilPainting expects uint8 BGR
        try:
            out = cv2.xphoto.oilPainting(img, size, dyn_ratio)
        except AttributeError:
            # xphoto not available — fall back to bilateral filter approximation
            out = cv2.bilateralFilter(img, size * 2 + 1, 75, 75)

        return self.to_float32(out)
