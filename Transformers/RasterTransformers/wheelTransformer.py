from .base import RasterTransformer 
import numpy as np # type: ignore
from PIL import Image, ImageChops # type: ignore
import random
import ScreenArt.log as log

class WheelTransformer(RasterTransformer):
    """
    Creates a wheel-like pattern by rotating half-height copies of the image 
    around the canvas center.
    """

    def __init__(self):
        super().__init__()
        
        # --- GENERATE PARAMETERS IN INIT ---
        self.num_copies = random.randint(3, 7)
        self.blend_mode = random.choice(["normal", "add", "lighter"])

        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "copies": self.num_copies,
            "blend": self.blend_mode
        }
        # -------------------------
        # Keeping this debug log for one more run to be sure

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:

        # 1. Convert incoming Numpy Array to PIL Image
        if isinstance(img_np, np.ndarray):
            img = Image.fromarray(img_np)
        elif isinstance(img_np, Image.Image):
            img = img_np.copy()
        else:
            log.warning(f"WheelTransformer received unknown type: {type(img_np)}")
            return img_np
        
        # 2. Prepare dimensions
        w, h = img.size
        
        # "Half height": Resize original to w, h/2
        spoke_h = h // 2
        spoke = img.resize((w, spoke_h), resample=Image.LANCZOS)
        spoke = spoke.convert("RGBA")

        # 3. Setup Canvas
        # For additive blending, start with black. For normal, start with transparent.
        if self.blend_mode in ['add', 'lighter']:
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        else:
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        
        cx, cy = w // 2, h // 2
        step_angle = 360.0 / self.num_copies

        # 4. Create the Wheel
        for i in range(self.num_copies):
            angle = i * step_angle
            
            # Rotate
            rotated_spoke = spoke.rotate(angle, expand=True, resample=Image.BICUBIC)
            
            # Calculate paste coordinates
            rw, rh = rotated_spoke.size
            paste_x = cx - (rw // 2)
            paste_y = cy - (rh // 2)
            
            if self.blend_mode == 'normal':
                # Standard Alpha Composition
                canvas.paste(rotated_spoke, (paste_x, paste_y), rotated_spoke)
            
            else:
                # For specialized blending, we create a full-size layer for the spoke
                layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                layer.paste(rotated_spoke, (paste_x, paste_y), rotated_spoke)
                
                # Apply Blend
                if self.blend_mode == 'add':
                    canvas = ImageChops.add(canvas, layer)
                elif self.blend_mode == 'lighter':
                    canvas = ImageChops.lighter(canvas, layer)

        # 5. FINAL STEP: Convert to RGB
        # This prevents the "cannot reshape array" error in bus.py
        # We use a black background to composite any remaining transparency
        bg = Image.new("RGB", (w, h), (0, 0, 0))
        bg.paste(canvas, (0, 0), mask=canvas)
        
        return np.array(bg)
