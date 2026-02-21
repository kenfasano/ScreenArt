import cv2 
import numpy as np 
import random
from PIL import Image 
from .rasterTransformer import RasterTransformer

POSSIBLE_NUM_COLORS: list[int] = [1, 2, 4, 8, 16, 32, 64, 128, 256]

class XrayTransformer(RasterTransformer):
    """
    Quantizes the image down to a limited palette of colors.
    """
    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("xraytransformer", {})

        num_colors = t_config.get("num_colors")
        if isinstance(num_colors, int) and num_colors in POSSIBLE_NUM_COLORS:
            self.num_colors = num_colors
        else:
            self.num_colors = random.choice(POSSIBLE_NUM_COLORS)
            
        self.metadata_dictionary["colors"] = self.num_colors

        # Handle grayscale vs color seamlessly
        if img_np.ndim == 2:
            img_rgb_pil = Image.fromarray(cv2.cvtColor(img_np, cv2.COLOR_GRAY2RGB))
        else:
            img_rgb_pil = Image.fromarray(cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB))

        quantized_img_pil = img_rgb_pil.quantize(colors=self.num_colors)
        quantized_img_np = cv2.cvtColor(np.array(quantized_img_pil), cv2.COLOR_RGB2BGR)

        return quantized_img_np
