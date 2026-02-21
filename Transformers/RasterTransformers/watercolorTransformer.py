import cv2 
import numpy as np 
import random
from .rasterTransformer import RasterTransformer

DEFAULT_DOWNSCALE_FACTOR = 0.5 

class WatercolorTransformer(RasterTransformer):
    """
    Applies a stylized watercolor filter using OpenCV edge-preserving smoothing.
    """
    def __init__(self):
        super().__init__()
        self.allowed_styles = ['monet', 'psychedelic']

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("watercolortransformer", {})

        self.style_name = t_config.get("style_name")
        if self.style_name not in self.allowed_styles:
            self.style_name = random.choice(self.allowed_styles)

        scale_factor = t_config.get("scale_factor", DEFAULT_DOWNSCALE_FACTOR)
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["style"] = self.style_name
        self.metadata_dictionary["scale"] = scale_factor
        
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
