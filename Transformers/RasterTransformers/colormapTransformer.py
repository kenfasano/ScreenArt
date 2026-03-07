import cv2 
import random
import numpy as np 
from .rasterTransformer import RasterTransformer

class ColormapTransformer(RasterTransformer):
    """
    Applies a randomly chosen (or strictly configured) OpenCV colormap.
    """
    def __init__(self):
        super().__init__()
        self.color_maps = {
            "autumn": cv2.COLORMAP_AUTUMN,
            "bone": cv2.COLORMAP_BONE,
            "jet": cv2.COLORMAP_JET,
            "winter": cv2.COLORMAP_WINTER,
            "rainbow": cv2.COLORMAP_RAINBOW,
            "ocean": cv2.COLORMAP_OCEAN,
            "summer": cv2.COLORMAP_SUMMER,
            "spring": cv2.COLORMAP_SPRING,
            "cool": cv2.COLORMAP_COOL,
            "hsv": cv2.COLORMAP_HSV,
            "pink": cv2.COLORMAP_PINK,
            "hot": cv2.COLORMAP_HOT
        }

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        # Access config directly via inheritance
        t_config = self.config.get("colormaptransformer", {})

        # Ensure the image is in a supported format
        img_np = self.to_uint8(img_np)

        # Convert to grayscale if it's a color image
        if img_np.ndim == 3 and img_np.shape[2] == 3:
            grayscale_img = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        else:
            grayscale_img = img_np

        # Check if the user specified a map in the config, otherwise pick randomly
        preferred_map = t_config.get("map")
        if preferred_map in self.color_maps:
            chosen_colormap_key = preferred_map
        else:
            chosen_colormap_key = random.choice(list(self.color_maps.keys()))
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["map"] = chosen_colormap_key

        self.chosen_colormap_value = self.color_maps[chosen_colormap_key]
        colored_img = cv2.applyColorMap(grayscale_img, self.chosen_colormap_value)

        return self.to_float32(colored_img)
