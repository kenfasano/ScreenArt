from PIL import Image # type: ignore
import cv2 # type: ignore
import numpy as np # type: ignore
from .base import RasterTransformer

class ColormapTransformer(RasterTransformer):
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

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        import common
        """
        Applies a randomly chosen OpenCV colormap to the input image.
        The image is first converted to grayscale if it's a color image.
        """
        self.config = common.get_config(config, "colormaptransformer")

        # Ensure the image is in a supported format
        if img_np.dtype != np.uint8:
            img_np = (img_np * 255).astype(np.uint8)

        # Convert to grayscale if it's a color image
        if img_np.ndim == 3 and img_np.shape[2] == 3:
            img_pil = Image.fromarray(img_np)
            grayscale_img = np.array(img_pil.convert('L'))
        else:
            grayscale_img = img_np

        chosen_colormap_key = np.random.choice(list(self.color_maps.keys()))
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "map": chosen_colormap_key
        }
        # -------------------------

        self.chosen_colormap_value = self.color_maps[chosen_colormap_key]
        colored_img = cv2.applyColorMap(grayscale_img, self.chosen_colormap_value)

        return colored_img
