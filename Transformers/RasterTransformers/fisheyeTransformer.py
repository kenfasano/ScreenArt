import numpy as np
import random
from .rasterTransformer import RasterTransformer
from scipy.ndimage import map_coordinates # type: ignore

# --- Default min/max values for randomization ---
MIN_STRENGTH = 0.2
MAX_STRENGTH = 0.8
MIN_ZOOM = 0.8
MAX_ZOOM = 1.2

class FisheyeTransformer(RasterTransformer):
    """
    Applies a radial "fisheye" lens distortion to the image.
    """
    
    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("fisheyetransformer", {})

        # --- Parameter Handling ---
        # Strength of the distortion
        self.strength = t_config.get("strength")
        if self.strength is None or not isinstance(self.strength, (int, float)):
            self.strength = random.uniform(MIN_STRENGTH, MAX_STRENGTH)

        # Zoom factor
        self.zoom = t_config.get("zoom")
        if self.zoom is None or not isinstance(self.zoom, (int, float)):
            self.zoom = random.uniform(0.5, 1.5)
            
        # Shape of the lens
        self.shape = t_config.get("shape")
        if self.shape not in ["circle", "oval"]:
            self.shape = random.choice(["circle", "oval"])
            
        # --- POPULATE METADATA ---
        self.metadata_dictionary["strength"] = round(self.strength, 2)
        self.metadata_dictionary["zoom"] = round(self.zoom, 2)
        self.metadata_dictionary["shape"] = self.shape

        if img_np.ndim < 2 or img_np.ndim > 3:
            self.log.error(f"Input image must be 2D or 3D, but got {img_np.ndim} dimensions.")
            return img_np

        H, W = img_np.shape[:2]
        center_y, center_x = H / 2, W / 2

        # 1. Determine Radii based on shape
        if self.shape == "oval":
            radius_x, radius_y = W / 2, H / 2
        else:
            min_dim = min(H, W)
            radius_x, radius_y = min_dim / 2, min_dim / 2

        # Avoid division by zero for 0-sized images
        radius_x = max(radius_x, 1e-6)
        radius_y = max(radius_y, 1e-6)

        # 2. Generate coordinate grid for the output image
        y_out, x_out = np.mgrid[0:H, 0:W]

        # 3. Normalize and center coordinates
        norm_x = (x_out - center_x) / radius_x
        norm_y = (y_out - center_y) / radius_y

        # 4. Calculate radial distance for each output pixel
        r_out = np.sqrt(norm_x**2 + norm_y**2)

        # 5. Apply fisheye distortion (inverse map)
        r_in = r_out / (1 + self.strength * r_out)
        
        # 6. Calculate scaling factor and apply zoom
        scale_factor = np.divide(r_in, r_out, out=np.ones_like(r_in), where=r_out != 0)
        scale_factor /= self.zoom

        norm_x_in = norm_x * scale_factor
        norm_y_in = norm_y * scale_factor

        # 7. De-normalize to get final source pixel coordinates
        y_in = (norm_y_in * radius_y) + center_y
        x_in = (norm_x_in * radius_x) + center_x

        displacement_map = (y_in, x_in)

        # 8. Apply transformation
        if img_np.ndim == 3:
            warped_img = np.zeros_like(img_np)
            for i in range(img_np.shape[2]):
                warped_img[:, :, i] = map_coordinates(
                    img_np[:, :, i],
                    displacement_map,
                    order=1,
                    mode='constant',
                    cval=0.0
                )
        else:
            warped_img = map_coordinates(
                img_np,
                displacement_map,
                order=1,
                mode='constant',
                cval=0.0
            )

        return warped_img.astype(img_np.dtype)
