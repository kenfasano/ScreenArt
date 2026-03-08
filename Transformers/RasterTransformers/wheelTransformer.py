from .rasterTransformer import RasterTransformer 
import numpy as np 
from PIL import Image, ImageChops 
import random

class WheelTransformer(RasterTransformer):
    """
    Creates a wheel-like pattern by rotating half-height copies of the image 
    around the canvas center.
    """
    def __init__(self):
        super().__init__()
        
        self.num_copies = random.randint(3, 5)  # capped from 7 to bound max runtime
        self.blend_mode = random.choice(["normal", "add", "lighter"])

        self.metadata_dictionary["copies"] = self.num_copies
        self.metadata_dictionary["blend"] = self.blend_mode

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:

        # 1. Convert incoming Numpy Array to PIL Image
        if isinstance(img_np, np.ndarray):
            img = Image.fromarray(self.to_uint8(img_np))
        elif isinstance(img_np, Image.Image):
            img = img_np.copy()
        else:
            self.log.warning(f"WheelTransformer received unknown type: {type(img_np)}")
            return img_np
        
        w, h = img.size
        
        # "Half height": Resize original to w, h/2
        spoke_h = h // 2
        spoke = img.resize((w, spoke_h), resample=Image.LANCZOS)
        spoke = spoke.convert("RGBA")

        # 3. Setup Canvas
        if self.blend_mode in ['add', 'lighter']:
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        else:
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        
        cx, cy = w // 2, h // 2
        step_angle = 360.0 / self.num_copies

        # 4. Create the Wheel
        for i in range(self.num_copies):
            angle = i * step_angle
            
            rotated_spoke = spoke.rotate(angle, expand=True, resample=Image.BILINEAR)
            
            rw, rh = rotated_spoke.size
            paste_x = cx - (rw // 2)
            paste_y = cy - (rh // 2)
            
            if self.blend_mode == 'normal':
                canvas.paste(rotated_spoke, (paste_x, paste_y), rotated_spoke)
            else:
                # Crop to the affected region only — avoids allocating a full (w,h) layer per copy
                rw, rh = rotated_spoke.size
                x1, y1 = max(0, paste_x), max(0, paste_y)
                x2, y2 = min(w, paste_x + rw), min(h, paste_y + rh)
                bg_crop  = canvas.crop((x1, y1, x2, y2))
                rot_crop = rotated_spoke.crop((x1-paste_x, y1-paste_y, x1-paste_x+(x2-x1), y1-paste_y+(y2-y1)))
                if self.blend_mode == 'add':
                    merged = ImageChops.add(bg_crop, rot_crop)
                elif self.blend_mode == 'lighter':
                    merged = ImageChops.lighter(bg_crop, rot_crop)
                canvas.paste(merged, (x1, y1))

        # 5. Convert to RGB to safely return to numpy pipeline
        bg = Image.new("RGB", (w, h), (0, 0, 0))
        bg.paste(canvas, (0, 0), mask=canvas)
        
        return self.to_float32(np.array(bg))
