import cv2 # type: ignore
import numpy as np # type: ignore
import random
from PIL import Image # type: ignore

from .base import RasterTransformer

POSSIBLE_NUM_COLORS: list[int] = [1,2,4,8,16,32,64,128,256]

class XrayTransformer(RasterTransformer):
    def __init__(self):
        super().__init__()

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        import common
        import log
        self.config = common.get_config(config, "xraytransformer")

        if self.config is None:
            log.error("config is None for XrayTransformer!")
            return img_np 

        num_colors = self.config.get("num_colors", "?")
        if isinstance(num_colors, int) and num_colors in POSSIBLE_NUM_COLORS:
            self.num_colors = num_colors
        else:
            self.num_colors = random.choice(POSSIBLE_NUM_COLORS)
            
        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "colors": self.num_colors
        }
        # -------------------------

        img_rgb_pil = Image.fromarray(cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB))

        quantized_img_pil = img_rgb_pil.quantize(colors=self.num_colors)

        quantized_img_np = cv2.cvtColor(np.array(quantized_img_pil), cv2.COLOR_RGB2BGR)

        return quantized_img_np
