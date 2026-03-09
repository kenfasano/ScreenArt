import numpy as np 
import random
import shutil
import os
import cv2 
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

        self._precompute_radial_fields()

    def _generate_initial_vertices(self, scale: float) -> np.ndarray:
        cx, cy = self.width / 2, self.height / 2
        radius = min(self.width, self.height) / 2 * scale
        
        angles = np.deg2rad([270, 30, 150]) 
        
        x = cx + radius * np.cos(angles)
        y = cy + radius * np.sin(angles) 
        return np.column_stack((x, y))

    def _precompute_radial_fields(self):
        h, w = self.height, self.width
        y, x = np.indices((h, w))

        cx, cy = w / 2, h / 2
        dx = x - cx
        dy = y - cy

        self._radius = np.sqrt(dx**2 + dy**2)
        self._angle = np.arctan2(dy, dx)

    def _create_image_with_opposite_bg(self, width: int, height: int, points: np.ndarray, hues: list[int]):
        cx, cy = width / 2, height / 2

        valid = (
            (points[:,0] >= 0) &
            (points[:,0] < width) &
            (points[:,1] >= 0) &
            (points[:,1] < height)
        )

        pts = points[valid]
        if pts.size == 0:
            return np.zeros((height, width, 3), dtype=np.uint8), (0,0,0)

        px = pts[:,0].astype(np.int32)
        py = pts[:,1].astype(np.int32)

        dx = px - cx
        dy = py - cy

        radii = np.sqrt(dx*dx + dy*dy)
        angles = np.arctan2(dy, dx)

        pattern = angles + (radii * 0.05)
        factor = (np.sin(pattern) + 1) * 0.5

        if len(hues) == 2:
            h1, h2 = hues
            point_hues = h1 + (h2 - h1) * factor
        else:
            h1, h2, h3 = hues[:3]
            mask = factor < 0.5
            point_hues = np.empty_like(factor)
            point_hues[mask] = h1 + (h2 - h1) * (factor[mask] * 2)
            point_hues[~mask] = h2 + (h3 - h2) * ((factor[~mask] - 0.5) * 2)

        hsv = np.zeros((len(point_hues), 1, 3), dtype=np.uint8)
        hsv[:,0,0] = point_hues.astype(np.uint8)
        hsv[:,0,1] = 200
        hsv[:,0,2] = 255

        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).reshape(-1,3)

        mean_color = rgb.mean(axis=0)
        bg = tuple((255 - mean_color).astype(np.uint8))

        img = np.full((height, width, 3), bg, dtype=np.uint8)
        img[py, px] = rgb

        return img, bg

    def run(self, *args, **kwargs):
        output_dir = os.path.join(self.config["paths"]["generators_in"], "kochsnowflake")
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        for i in range(self.file_count):
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
                
            filename_suffix = f"_{i+1}.jpeg" if self.file_count > 1 else ".jpeg"
            filename = os.path.join(output_dir, f"{self.base_filename}{filename_suffix}")
                
            img, bg_color = self._create_image_with_opposite_bg(self.width, self.height, cloud, current_hues)
            img_arr, bg_color = self._create_image_with_opposite_bg(self.width, self.height, cloud, current_hues)

            try:
                Image.fromarray(img_arr).save(filename, quality=95)
                self.log.debug(f"Generated KS4: {filename} (Points: {num_points}, Spiral: {spiral_tightness:.2f}, BG: {bg_color})")
            except Exception as e:
                self.log.debug(f"Failed to save {filename}: {e}")
