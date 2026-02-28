import numpy as np 
import random
import shutil
import os
import cv2 
import time
from PIL import Image 
from .drawGenerator import DrawGenerator
from ..Transformers.LinearTransformers.randomSierpinskiTransformer import RandomSierpinskiTransformer
from ..Transformers.LinearTransformers.spiralTransformer import SpiralTransformer

class KochSnowflake4(DrawGenerator):
    """
    Generates Sierpinski Triangles using the Chaos Game (Random Point Cloud).
    The background color is calculated to be the opposite of the fractal's average color.
    """
    def __init__(self):
        super().__init__()
        
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = int(self.config.get('file_count', 5))
        self.base_filename = "koch_snowflake_4"
        
        self.chaos_transformer = RandomSierpinskiTransformer(num_points=100000)
        self.spiral_transformer = SpiralTransformer(tightness=0.8) 

    def _generate_initial_vertices(self, scale: float) -> np.ndarray:
        cx, cy = self.width / 2, self.height / 2
        radius = min(self.width, self.height) / 2 * scale
        
        angles = np.deg2rad([270, 30, 150]) 
        
        x = cx + radius * np.cos(angles)
        y = cy + radius * np.sin(angles) 
        return np.column_stack((x, y))

    def _create_image_with_opposite_bg(self, width: int, height: int, points: np.ndarray, hues: list[int]) -> tuple[Image.Image, tuple]:
        cx, cy = width / 2, height / 2
        
        valid_mask = (points[:,0] >= 0) & (points[:,0] < width) & (points[:,1] >= 0) & (points[:,1] < height)
        valid_points = points[valid_mask].astype(int)
        
        if valid_points.size == 0:
            return Image.new('RGB', (width, height), (0,0,0)), (0,0,0)

        px, py = valid_points[:, 0], valid_points[:, 1]
        dx, dy = px - cx, py - cy
        radii = np.sqrt(dx**2 + dy**2)
        angles = np.arctan2(dy, dx)
        
        pattern = angles + (radii * 0.05)
        factor = (np.sin(pattern) + 1) / 2
        
        if len(hues) == 2:
            h1, h2 = hues
            point_hues = h1 + (h2 - h1) * factor
        elif len(hues) >= 3:
            h1, h2, h3 = hues[:3]
            point_hues = np.zeros_like(factor)
            mask1 = factor < 0.5
            mask2 = ~mask1
            point_hues[mask1] = h1 + (h2 - h1) * factor[mask1] * 2
            point_hues[mask2] = h2 + (h3 - h2) * (factor[mask2] - 0.5) * 2
        else:
            point_hues = factor * 180
            
        h_channel = point_hues.astype(np.uint8)
        s_channel, v_channel = np.full_like(h_channel, 200), np.full_like(h_channel, 255)
        
        hsv_points = np.stack([h_channel, s_channel, v_channel], axis=1).reshape(-1, 1, 3)
        rgb_points = cv2.cvtColor(hsv_points, cv2.COLOR_HSV2RGB).reshape(-1, 3)
        
        # Calculate the mean and convert to native Python integers during the subtraction
        mean_color = np.mean(rgb_points, axis=0)
        
        # Explicitly extract R, G, B and convert to native Python integers
        opposite_bg = (
            int(255 - mean_color[0]),
            int(255 - mean_color[1]),
            int(255 - mean_color[2])
        )

        img = Image.new('RGB', (width, height), opposite_bg)
        arr = np.array(img)
        arr[py, px] = rgb_points
        
        return Image.fromarray(arr), opposite_bg

    def run(self, *args, **kwargs):
        with self.timer():
            output_dir = os.path.join(self.config["paths"]["generators_in"], "kochsnowflake")
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            os.makedirs(output_dir, exist_ok=True)

            for i in range(self.file_count):
                random.seed(time.perf_counter() + i)

                spiral_tightness = random.uniform(0.5, 2.0) 
                num_points = random.choice([50000, 100000, 200000])
                
                num_colors = random.choice([2, 3])
                current_hues = [random.randint(0, 180) for _ in range(num_colors)]
                
                self.chaos_transformer.num_points = num_points
                self.spiral_transformer.tightness = spiral_tightness
                
                scale = random.uniform(0.6, 0.9)
                vertices = self._generate_initial_vertices(scale)
                
                cloud = self.chaos_transformer.run(vertices) 
                cloud = self.spiral_transformer.run(cloud) 
                
                img, bg_color = self._create_image_with_opposite_bg(self.width, self.height, cloud, current_hues)

                filename_suffix = f"_{i+1}.jpg" if self.file_count > 1 else ".jpg"
                filename = os.path.join(output_dir, f"{self.base_filename}{filename_suffix}")
                
                try:
                    img.save(filename)
                    self.log.debug(f"Generated KS4: {filename} (Points: {num_points}, Spiral: {spiral_tightness:.2f}, BG: {bg_color})")
                except Exception as e:
                    self.log.debug(f"Failed to save {filename}: {e}")
