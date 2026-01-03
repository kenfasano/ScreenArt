import numpy as np # type: ignore
import random
import time
import shutil
import os
import cv2 # type: ignore
from PIL import Image, ImageDraw # type: ignore
from . import drawGenerator
from .. import common
from .. import log

# Import Transformers
try:
    from Transformers.LinearTransformers.randomSierpinskiTransformer import RandomSierpinskiTransformer
    from Transformers.LinearTransformers.spiralTransformer import SpiralTransformer
except ImportError:
    from ..Transformers.LinearTransformers.randomSierpinskiTransformer import RandomSierpinskiTransformer
    from ..Transformers.LinearTransformers.spiralTransformer import SpiralTransformer

class KochSnowflake4(drawGenerator.DrawGenerator):
    """
    Generates Sierpinski Triangles using the Chaos Game (Random Point Cloud).
    The background color is calculated to be the opposite of the fractal's average color.
    """
    def __init__(self, config: dict | None):
        super().__init__()
        self.config = (config.get("kochSnowflake") if config else {}) or {}
        
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = int(self.config.get('file_count', 5))
        self.base_filename = "koch_snowflake_4"
        
        # High point count for good definition
        self.chaos_transformer = RandomSierpinskiTransformer(num_points=100000)
        self.spiral_transformer = SpiralTransformer(tightness=0.8) 

    def _generate_initial_vertices(self, scale: float) -> np.ndarray:
        cx, cy = self.width / 2, self.height / 2
        radius = min(self.width, self.height) / 2 * scale
        
        # Equilateral Triangle Vertices
        angles = np.deg2rad([270, 30, 150]) # Top, BottomRight, BottomLeft
        
        x = cx + radius * np.cos(angles)
        y = cy + radius * np.sin(angles) 
        return np.column_stack((x, y))

    def _create_image_with_opposite_bg(self, width: int, height: int, points: np.ndarray, hues: list[int]) -> Image.Image:
        """
        Calculates point colors, determines the average color, finds its opposite,
        fills the background, and then draws the points.
        """
        cx, cy = width / 2, height / 2
        
        # 1. Filter points inside canvas
        valid_mask = (points[:,0] >= 0) & (points[:,0] < width) & (points[:,1] >= 0) & (points[:,1] < height)
        valid_points = points[valid_mask].astype(int)
        
        if valid_points.size == 0:
            return Image.new('RGB', (width, height), (0,0,0))

        # 2. Calculate geometric properties for point coloring
        px = valid_points[:, 0]
        py = valid_points[:, 1]
        
        dx = px - cx
        dy = py - cy
        radii = np.sqrt(dx**2 + dy**2)
        angles = np.arctan2(dy, dx)
        
        # 3. Spiral Pattern & Hue Interpolation Logic
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
            
        # 4. Create RGB colors for all points
        h_channel = point_hues.astype(np.uint8)
        s_channel = np.full_like(h_channel, 200)
        v_channel = np.full_like(h_channel, 255)
        
        hsv_points = np.stack([h_channel, s_channel, v_channel], axis=1)
        hsv_points_img = hsv_points.reshape(-1, 1, 3)
        rgb_points = cv2.cvtColor(hsv_points_img, cv2.COLOR_HSV2RGB).reshape(-1, 3)
        
        # 5. Calculate Opposite Background Color
        # Average color of all points
        avg_rgb = np.mean(rgb_points, axis=0).astype(int)
        # Invert the average to get the opposite color
        opposite_bg = tuple(255 - avg_rgb)

        # 6. Create Image and Draw
        # Start with the calculated opposite background
        img = Image.new('RGB', (width, height), opposite_bg)
        arr = np.array(img)
        
        # Assign colors to image array (y is row, x is col)
        arr[py, px] = rgb_points
        
        return Image.fromarray(arr), opposite_bg

    def draw(self):
        output_dir = f"{common.INPUT_SOURCES_IN}/KochSnowflake"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        for i in range(self.file_count):
            random.seed(time.perf_counter() + i)

            # Random Settings
            spiral_tightness = random.uniform(0.5, 2.0) 
            num_points = random.choice([50000, 100000, 200000])
            
            # Colors (Hues for the points)
            num_colors = random.choice([2, 3])
            current_hues = [random.randint(0, 180) for _ in range(num_colors)]
            
            # Setup Transformers
            self.chaos_transformer.num_points = num_points
            self.spiral_transformer.tightness = spiral_tightness
            
            # 1. Generate Geometry
            scale = random.uniform(0.6, 0.9)
            vertices = self._generate_initial_vertices(scale)
            cloud = self.chaos_transformer.apply({}, vertices) # type: ignore
            cloud = self.spiral_transformer.apply({}, cloud) # type: ignore
            
            # 2. Create Image with Opposite Background
            # We no longer generate a random BG color here; it's calculated inside the method.
            img, bg_color = self._create_image_with_opposite_bg(self.width, self.height, cloud, current_hues)

            # 3. Save
            if self.file_count == 1:
                filename = f"{output_dir}/{self.base_filename}.jpg"
            else:
                filename = f"{output_dir}/{self.base_filename}_{i+1}.jpg"
            
            img.save(filename, 'JPEG')
            hue_str = ">".join(map(str, current_hues))
            # Log the calculated background color
            log.info(f"Generated KS4: {filename} (Points: {num_points}, Spiral: {spiral_tightness:.2f}, BG: {bg_color})")
