import cv2 # type: ignore
import numpy as np # type: ignore
import random
from .base import RasterTransformer

DEFAULT_EXTRUSION_INTENSITY = 0.5

class ThreeDExtrusionTransformer(RasterTransformer):
    """
    Converts image brightness into depth to create a pseudo-3D bas-relief effect.
    Optimized using vectorized NumPy and OpenCV operations.
    """
    def __init__(self):
        super().__init__()

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        import ScreenArt.common as common
        import ScreenArt.log as log
        self.config = common.get_config(config, "threedextrusiontransformer")

        if self.config is None:
            log.error("config is None for ThreeDExtrusionTransformer!")
            return img_np 

        # --- Parameter Handling ---
        extrusion_intensity = self.config.get("extrusion_intensity", DEFAULT_EXTRUSION_INTENSITY)
        if not isinstance(extrusion_intensity, (int, float)):
             extrusion_intensity = DEFAULT_EXTRUSION_INTENSITY
        
        # Clamp and prevent division by zero (epsilon)
        extrusion_intensity = max(0.001, min(1.0, float(extrusion_intensity)))

        ambient_light = self.config.get("ambient_light", None)
        if isinstance(ambient_light, str):
             # Handle randomized string input if present
             ambient_light = random.uniform(0.0, 1.0)
        elif not isinstance(ambient_light, (int, float)):
             ambient_light = 0.3
             
        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "intensity": extrusion_intensity,
            "ambient": ambient_light
        }
        # -------------------------
        
        # --- Optimized Pipeline ---
        
        # 1. Grayscale Conversion (Standard weighted conversion)
        if img_np.ndim == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY).astype(np.float32)
        else:
            gray = img_np.astype(np.float32)

        # 2. Gaussian/Mean Blur
        blurred = cv2.blur(gray, (3, 3))

        # 3. Gradient Calculation (Surface Slope)
        grad_x = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=1) / 2.0
        grad_y = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=1) / 2.0

        # 4. Surface Normal Calculation (Vectorized)
        normal_z = 1.0 / extrusion_intensity
        magnitude = np.sqrt(grad_x**2 + grad_y**2 + normal_z**2)
        
        nx = -grad_x / magnitude
        ny = -grad_y / magnitude
        nz = normal_z / magnitude

        # 5. Lighting Calculation
        lx, ly, lz = 1.0, 1.0, -1.0
        lm = np.sqrt(lx**2 + ly**2 + lz**2)
        lx, ly, lz = lx/lm, ly/lm, lz/lm

        dot_product = (nx * lx) + (ny * ly) + (nz * lz)

        # 6. Phong Shading (Simplified)
        shading = ambient_light + (1.0 - ambient_light) * dot_product
        np.clip(shading, 0.0, 1.0, out=shading)

        # 7. Apply to Image
        shading = shading[..., np.newaxis]
        output_np = (img_np * shading).astype(np.uint8)

        return output_np
