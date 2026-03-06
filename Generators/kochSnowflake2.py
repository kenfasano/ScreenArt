import numpy as np 
import random
import shutil
import os
import cv2 
from PIL import Image
from .drawGenerator import DrawGenerator
from ..Transformers.LinearTransformers.sierpinskiTransformer import SierpinskiTransformer
from ..Transformers.LinearTransformers.spiralTransformer import SpiralTransformer

class KochSnowflake2(DrawGenerator):
    def __init__(self):
        super().__init__()
        
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = int(self.config.get('file_count', 5))
        self.base_filename = "koch_snowflake_2"
        
        self.sierpinski_transformer = SierpinskiTransformer()
        self.spiral_transformer = SpiralTransformer(tightness=0.8) 
        
        self._precompute_radial_fields()

    def _precompute_radial_fields(self):
        h, w = self.height, self.width
        y, x = np.indices((h, w), dtype=np.float32)

        cx, cy = w / 2, h / 2
        dx = x - cx
        dy = y - cy

        self._radius = np.sqrt(dx * dx + dy * dy)
        self._angle = np.arctan2(dy, dx)

    def _generate_initial_triangle(self, scale: float) -> np.ndarray:
        cx, cy = self.width / 2, self.height / 2
        radius = min(self.width, self.height) / 2 * scale
        angles = np.deg2rad([270, 30, 150, 270]) 
        x = cx + radius * np.cos(angles)
        y = cy + radius * np.sin(angles) 
        return np.column_stack((x, y)).astype(np.float32)

    def _apply_psychedelic_mask(self, arr, hues, bg_color):
        radius = self._radius
        angle = self._angle

        pattern = angle + (radius * 0.05)
        factor = (np.sin(pattern) + 1) * 0.5

        if len(hues) == 2:
            h1, h2 = hues
            hue_map = h1 + (h2 - h1) * factor
        elif len(hues) >= 3:
            h1, h2, h3 = hues[:3]
            mask1 = factor < 0.5
            hue_map = np.empty_like(factor)
            hue_map[mask1] = h1 + (h2 - h1) * (factor[mask1] * 2)
            hue_map[~mask1] = h2 + (h3 - h2) * ((factor[~mask1] - 0.5) * 2)
        else:
            hue_map = factor * 180

        value_channel = arr.max(axis=2)
        mask = value_channel > 20

        hsv = np.empty((self.height, self.width, 3), dtype=np.uint8)
        hsv[..., 0] = hue_map.astype(np.uint8)
        hsv[..., 1] = 200
        hsv[..., 2] = value_channel

        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        result = np.full_like(arr, bg_color)
        result[mask] = rgb[mask]

        return result

    def run(self, *args, **kwargs): 
        output_dir = os.path.join(self.config["paths"]["generators_in"], "kochsnowflake")
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        for i in range(self.file_count):
            num_transforms = random.randint(4, 7) 
            spiral_tightness = random.uniform(0.3, 1.2)
                
            num_colors = random.choice([2, 3])
            current_hues = [random.randint(0, 180) for _ in range(num_colors)]
            bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                
            self.spiral_transformer.tightness = spiral_tightness
            current_scale = random.uniform(0.5, 0.8)
                
            points = self._generate_initial_triangle(current_scale)

            # --- USING NEW .run() CONTRACT ---
            for _ in range(num_transforms):
                points = self.sierpinski_transformer.run(points) 
            points = self.spiral_transformer.run(points) 

            img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            poly = points.astype(np.int32)
            cv2.fillPoly(img, [poly], (255, 255, 255))

            img = self._apply_psychedelic_mask(img, current_hues, bg_color)

            filename_suffix = f"_{i+1}.jpeg" if self.file_count > 1 else ".jpeg"
            filename = os.path.join(output_dir, f"{self.base_filename}{filename_suffix}")
                
            try:
                Image.fromarray(img).save(filename, quality=95)
                hue_str = ">".join(map(str, current_hues))
                self.log.debug(f"Generated KS2: {filename} (Iter: {num_transforms}, Spiral: {spiral_tightness:.2f}, Hues: {hue_str})")
            except Exception as e:
                self.log.debug(f"Failed to save {filename}: {e}")
