import cv2 # type: ignore
import numpy as np # type: ignore
import random
from .base import RasterTransformer
from Transformers.transformer_dictionary import transformer_styles, transformer_ids

DEFAULT_DOWNSCALE_FACTOR = 0.5 

class WatercolorTransformer(RasterTransformer):
    def __init__(self):
        super().__init__()

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        import common
        self.config = common.get_config(config, "watercolortransformer")
        
        if self.config is None:
            self.config = {}

        self.transformer_id = transformer_ids.get(self.__class__.__name__, None)
        if self.transformer_id and self.transformer_id in transformer_styles:
             self.allowed_styles = list(transformer_styles[self.transformer_id].keys())
        else:
             self.allowed_styles = ['monet', 'psychedelic']

        self.style_name = self.config.get("style_name", None)
        if self.style_name is None or self.style_name == "?":
            self.style_name = random.choice(self.allowed_styles)

        scale_factor = self.config.get("scale_factor", DEFAULT_DOWNSCALE_FACTOR)
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "style": self.style_name,
            "scale": scale_factor
        }
        # -------------------------
        
        if self.style_name == 'monet':
            sigma_s = random.uniform(60 * 0.8, 60 * 1.2)
            sigma_r = random.uniform(0.45 * 0.8, 0.45 * 1.2)
        else: # psychedelic
            sigma_s = random.uniform(150, 200)
            sigma_r = random.uniform(0.8, 0.95)

        h, w = img_np.shape[:2]
        new_w, new_h = int(w * scale_factor), int(h * scale_factor)
        should_resize = scale_factor < 1.0 and new_w > 100 and new_h > 100
        
        if should_resize:
            processing_img = cv2.resize(img_np, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            sigma_s = sigma_s * scale_factor
        else:
            processing_img = img_np

        stylized = cv2.stylization(processing_img, sigma_s=sigma_s, sigma_r=sigma_r)

        hsv = cv2.cvtColor(stylized, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        if self.style_name == 'monet':
            hsv[..., 1] *= 1.15
            hsv[..., 2] = hsv[..., 2] * 1.05 + 10
        else: # psychedelic
            hsv[..., 1] *= 1.5
            hsv[..., 2] = hsv[..., 2] * 1.2 + 30

        np.clip(hsv, 0, 255, out=hsv)
        hsv = hsv.astype(np.uint8)
        result_small = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        if should_resize:
            output_np = cv2.resize(result_small, (w, h), interpolation=cv2.INTER_LINEAR)
        else:
            output_np = result_small

        return output_np
