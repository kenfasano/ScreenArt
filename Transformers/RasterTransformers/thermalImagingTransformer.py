import numpy as np
import cv2 
from .rasterTransformer import RasterTransformer

class ThermalImagingTransformer(RasterTransformer):
    """
    Applies a thermal imaging effect to the input image by
    converting it to grayscale and applying a custom colormap.
    """
    def __init__(self):
        super().__init__()
        self.colormap = self._create_thermal_colormap()

    def _create_thermal_colormap(self) -> np.ndarray:
        # A simple linear interpolation for a thermal-like palette
        colormap = np.zeros((256, 3), dtype=np.uint8)
        
        # Black to Red (0-63)
        colormap[0:64, 0] = np.linspace(0, 255, 64)
        
        # Red to Yellow (64-127)
        colormap[64:128, 0] = 255
        colormap[64:128, 1] = np.linspace(0, 255, 64)

        # Yellow to White (128-255)
        colormap[128:256, 0] = 255
        colormap[128:256, 1] = 255
        colormap[128:256, 2] = np.linspace(0, 255, 128)
        
        return colormap

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        img_np = self.to_uint8(img_np)

        if img_np.ndim == 3 and img_np.shape[2] == 3:
            grayscale_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            grayscale_img = img_np

        # Histogram stretch so the full thermal palette is used regardless of source brightness
        p_low, p_high = np.percentile(grayscale_img, (2, 98))
        if p_high > p_low:
            grayscale_img = np.clip((grayscale_img.astype(np.float32) - p_low) / (p_high - p_low) * 255, 0, 255).astype(np.uint8)

        self.metadata_dictionary["thermal"] = True

        return self.to_float32(self.colormap[grayscale_img])
