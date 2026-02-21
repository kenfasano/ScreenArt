import cv2 
import numpy as np 
import random
from .rasterTransformer import RasterTransformer

DEFAULT_EXTRUSION_INTENSITY = 0.5

class ThreeDExtrusionTransformer(RasterTransformer):
    """
    Converts image brightness into depth to create a pseudo-3D bas-relief effect.
    Optimized using vectorized NumPy and OpenCV operations.
    """
    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("threedextrusiontransformer", {})

        # --- Parameter Handling ---
        extrusion_intensity = t_config.get("extrusion_intensity", DEFAULT_EXTRUSION_INTENSITY)
        if not isinstance(extrusion_intensity, (int, float)):
             extrusion_intensity = DEFAULT_EXTRUSION_INTENSITY
        
        # Clamp and prevent division by zero (epsilon)
        extrusion_intensity = max(0.001, min(1.0, float(extrusion_intensity)))

        ambient_light = t_config.get("ambient_light")
        if isinstance(ambient_light, str):
             ambient_light = random.uniform(0.0, 1.0)
        elif not isinstance(ambient_light, (int, float)):
             ambient_light = 0.3
             
        # --- POPULATE METADATA ---
        self.metadata_dictionary["intensity"] = round(extrusion_intensity, 3)
        self.metadata_dictionary["ambient"] = round(ambient_light, 2)
        
        # --- Optimized Pipeline ---
        if img_np.ndim == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY).astype(np.float32)
        else:
            gray = img_np.astype(np.float32)

        # Gaussian/Mean Blur
        blurred = cv2.blur(gray, (3, 3))

        # Gradient Calculation (Surface Slope)
        grad_x = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=1) / 2.0
        grad_y = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=1) / 2.0

        # Surface Normal Calculation (Vectorized)
        normal_z = 1.0 / extrusion_intensity
        magnitude = np.sqrt(grad_x**2 + grad_y**2 + normal_z**2)
        
        nx = -grad_x / magnitude
        ny = -grad_y / magnitude
        nz = normal_z / magnitude

        # Lighting Calculation
        lx, ly, lz = 1.0, 1.0, -1.0
        lm = np.sqrt(lx**2 + ly**2 + lz**2)
        lx, ly, lz = lx/lm, ly/lm, lz/lm

        dot_product = (nx * lx) + (ny * ly) + (nz * lz)

        # Phong Shading (Simplified)
        shading = ambient_light + (1.0 - ambient_light) * dot_product
        np.clip(shading, 0.0, 1.0, out=shading)

        # Apply to Image
        shading = shading[..., np.newaxis]
        output_np = (img_np * shading).astype(np.uint8)

        return output_np
