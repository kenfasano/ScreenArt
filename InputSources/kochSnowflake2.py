import numpy as np # type: ignore
import random
import time
import shutil
import os
import cv2 # type: ignore
from PIL import Image, ImageDraw # type: ignore
from . import drawInputSource
from .. import common
from .. import log

# Import Linear Transformers
try:
    from Transformers.LinearTransformers.sierpinskiTransformer import SierpinskiTransformer
    from Transformers.LinearTransformers.spiralTransformer import SpiralTransformer
except ImportError:
    from ..Transformers.LinearTransformers.sierpinskiTransformer import SierpinskiTransformer
    from ..Transformers.LinearTransformers.spiralTransformer import SpiralTransformer

class KochSnowflake2(drawInputSource.DrawInputSource):
    """
    Generates Sierpinski-style fractal images with Spiral distortion and Psychedelic coloring.
    """
    def __init__(self, config: dict | None):
        super().__init__()
        self.config = (config.get("kochSnowflake") if config else {}) or {}
        
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = int(self.config.get('file_count', 5))
        self.base_filename = "koch_snowflake_2"
        
        # Instantiate Transformers
        self.sierpinski_transformer = SierpinskiTransformer()
        self.spiral_transformer = SpiralTransformer(tightness=0.8) 

    def _generate_initial_triangle(self, scale: float) -> np.ndarray:
        cx, cy = self.width / 2, self.height / 2
        radius = min(self.width, self.height) / 2 * scale
        
        # Triangle pointing UP (270 degrees in image coords where 0 is right, 90 is down)
        # Angles: Top(270), BottomRight(30), BottomLeft(150)
        angles = np.deg2rad([270, 30, 150, 270]) 
        
        x = cx + radius * np.cos(angles)
        y = cy + radius * np.sin(angles) 
        return np.column_stack((x, y))

    def _apply_psychedelic_mask(self, img: Image.Image, hues: list[int], bg_color: tuple[int, int, int]) -> Image.Image:
        arr = np.array(img)
        h, w, _ = arr.shape
        y, x = np.indices((h, w))
        
        cx, cy = w / 2, h / 2
        dx = x - cx
        dy = y - cy
        radius = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx)
        
        # Spiral Pattern
        pattern = angle + (radius * 0.05) 
        factor = (np.sin(pattern) + 1) / 2 
        
        if len(hues) == 2:
            h1, h2 = hues
            hue_map = h1 + (h2 - h1) * factor
        elif len(hues) >= 3:
            h1, h2, h3 = hues[:3]
            hue_map = np.zeros_like(factor)
            mask1 = factor < 0.5
            mask2 = ~mask1
            f1 = factor[mask1] * 2
            hue_map[mask1] = h1 + (h2 - h1) * f1
            f2 = (factor[mask2] - 0.5) * 2
            hue_map[mask2] = h2 + (h3 - h2) * f2
        else:
            hue_map = factor * 180

        value_channel = np.max(arr, axis=2)
        mask = value_channel > 20 
        
        final_hsv = np.zeros((h, w, 3), dtype=np.uint8)
        final_hsv[..., 0] = hue_map.astype(np.uint8)
        final_hsv[..., 1] = 200 
        final_hsv[..., 2] = value_channel 
        
        final_rgb = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2RGB)
        
        # Use the random background color
        result_arr = np.zeros_like(arr)
        result_arr[:] = bg_color
        result_arr[mask] = final_rgb[mask]
        
        return Image.fromarray(result_arr)

    def draw(self):
        output_dir = f"{common.INPUT_SOURCES_IN}/KochSnowflake"

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        for i in range(self.file_count):
            random.seed(time.perf_counter() + i)

            # Randomize Settings
            num_transforms = random.randint(4, 7) # Sierpinski needs more iterations than Koch
            spiral_tightness = random.uniform(0.3, 1.2)
            
            # Randomize Colors
            num_colors = random.choice([2, 3])
            current_hues = [random.randint(0, 180) for _ in range(num_colors)]
            bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            
            self.spiral_transformer.tightness = spiral_tightness
            current_scale = random.uniform(0.5, 0.8)
            
            # 1. Start with Triangle
            points = self._generate_initial_triangle(current_scale)

            # 2. Apply Sierpinski Recursion
            for _ in range(num_transforms):
                points = self.sierpinski_transformer.apply({}, points) # type: ignore
                
            # 3. Apply Spiral Twist
            points = self.spiral_transformer.apply({}, points) # type: ignore

            # 4. Rasterize
            img = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            poly_coords = [tuple(p) for p in points]
            # No outline for Sierpinski - it looks cleaner as filled dots/triangles
            draw.polygon(poly_coords, fill=(255, 255, 255), outline=None)

            # 5. Apply Mask
            img = self._apply_psychedelic_mask(img, current_hues, bg_color)

            # 6. Save
            if self.file_count == 1:
                filename = f"{output_dir}/{self.base_filename}.jpg"
            else:
                filename = f"{output_dir}/{self.base_filename}_{i+1}.jpg"
            
            img.save(filename, 'JPEG')
            
            hue_str = ">".join(map(str, current_hues))
            log.info(f"Generated KS2: {filename} (Iter: {num_transforms}, Spiral: {spiral_tightness:.2f}, Hues: {hue_str}, BG: {bg_color})")
