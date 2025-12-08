import numpy as np # type: ignore
from PIL import Image # type: ignore
from .base import RasterTransformer

class ThermalImagingTransformer(RasterTransformer):
    def __init__(self):
        super().__init__()

    def _create_thermal_colormap(self) -> np.ndarray:
        # A simple linear interpolation for a thermal-like palette
        # from cold (dark) to hot (light).
        # You can use more complex pre-defined colormaps from libraries like matplotlib or OpenCV.
        # This one goes from black -> red -> yellow -> white.

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

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        """
        Applies a thermal imaging effect to the input image by
        converting it to grayscale and applying a colormap.
        """

        # Ensure the image is in a supported format (e.g., uint8)
        if img_np.dtype != np.uint8:
            img_np = (img_np * 255).astype(np.uint8)

        # Convert to grayscale first. This is a crucial step as
        # thermal imaging is based on a single "temperature" channel.
        # The `Image.fromarray` and `.convert('L')` are a simple way to do this.
        if img_np.ndim == 3 and img_np.shape[2] == 3:
            img_pil = Image.fromarray(img_np)
            grayscale_img = np.array(img_pil.convert('L'))
        else:
            grayscale_img = img_np
            
        # Define a thermal colormap. You can customize this array.
        # This example uses a simplified version of a 'ironbow' or 'lava' palette.
        self.colormap = self._create_thermal_colormap()

        # Apply the colormap.
        thermal_img_np = self.colormap[grayscale_img]
        return thermal_img_np

