import numpy as np # type: ignore
import random
import time
import shutil
import os
import cv2 # type: ignore
from PIL import Image, ImageDraw # type: ignore
from . import drawGenerator
from .. import log
from typing import Any # Import Any for flexible dicts

# 1. Import Linear Transformers
try:
    from Transformers.LinearTransformers.kochSnowflakeTransformer import KochSnowflakeTransformer
    from Transformers.LinearTransformers.spiralTransformer import SpiralTransformer
except ImportError:
    from ..Transformers.LinearTransformers.kochSnowflakeTransformer import KochSnowflakeTransformer
    from ..Transformers.LinearTransformers.spiralTransformer import SpiralTransformer

class KochSnowflake1(drawGenerator.DrawGenerator):
    """
    Generates Koch Snowflake fractal images with Spiral distortion and Psychedelic coloring.
    """
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = int(self.config.get('file_count', 5))
        self.base_filename = "koch_snowflake_1"
        
        # Instantiate Transformers
        self.koch_transformer = KochSnowflakeTransformer()
        self.spiral_transformer = SpiralTransformer(tightness=0.8) 

    def _generate_initial_triangle(self, scale: float) -> np.ndarray:
        cx, cy = self.width / 2, self.height / 2
        radius = min(self.width, self.height) / 2 * scale
        angles = np.deg2rad([90, 210, 330, 90]) 
        x = cx + radius * np.cos(angles)
        y = cy - radius * np.sin(angles)
        return np.column_stack((x, y))

    def _apply_psychedelic_mask(self, img: Image.Image, hues: list[int], bg_color: tuple[int, int, int]) -> Image.Image:
        """
        Applies a 'Psychedelic Mask' using a specific list of Hues.
        Interpolates between the provided hues based on the spiral geometry.
        Fills the background with the provided bg_color.
        """
        arr = np.array(img)
        h, w, _ = arr.shape
        y, x = np.indices((h, w))
        
        # Center coordinates
        cx, cy = w / 2, h / 2
        
        # Polar conversion
        dx = x - cx
        dy = y - cy
        radius = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx)
        
        # Create Pattern: Spiral
        # Angle gives basic wheel, Radius twists it
        pattern = angle + (radius * 0.05) 
        
        # Normalize pattern to 0..1 oscillating wave (Sine)
        factor = (np.sin(pattern) + 1) / 2 
        
        # Calculate Hue Map based on provided palette
        if len(hues) == 2:
            # Linear Interpolation: Hue1 -> Hue2 -> Hue1
            h1, h2 = hues
            hue_map = h1 + (h2 - h1) * factor
            
        elif len(hues) >= 3:
            # Multi-point Interpolation: Hue1 -> Hue2 -> Hue3 ...
            h1, h2, h3 = hues[:3]
            
            # Create masks for first half (0-0.5) and second half (0.5-1.0) of the wave
            hue_map = np.zeros_like(factor)
            mask1 = factor < 0.5
            mask2 = ~mask1
            
            # Map 0..0.5 to h1..h2
            f1 = factor[mask1] * 2
            hue_map[mask1] = h1 + (h2 - h1) * f1
            
            # Map 0.5..1.0 to h2..h3
            f2 = (factor[mask2] - 0.5) * 2
            hue_map[mask2] = h2 + (h3 - h2) * f2
        else:
            # Fallback
            hue_map = factor * 180

        # Extract Value channel (brightness) from original image to keep the shape
        value_channel = np.max(arr, axis=2)
        mask = value_channel > 20 # Threshold to identify shape vs background
        
        # Build HSV Image
        final_hsv = np.zeros((h, w, 3), dtype=np.uint8)
        final_hsv[..., 0] = hue_map.astype(np.uint8) # Computed Hue
        final_hsv[..., 1] = 200 # Fixed High Saturation
        final_hsv[..., 2] = value_channel # Original Value
        
        # Convert to RGB
        final_rgb = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2RGB)
        
        # Composite: Put psychedelic colors only where the snowflake is
        # Use random background color for the rest
        result_arr = np.zeros_like(arr)
        result_arr[:] = bg_color
        
        result_arr[mask] = final_rgb[mask]
        
        return Image.fromarray(result_arr)

    def draw(self):
        output_dir = f"{self.paths["generators_in"]}/KochSnowflake"

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        for i in range(self.file_count):
            random.seed(time.perf_counter() + i)

            # Randomize Settings
            num_transforms = random.randint(3, 5)
            spiral_tightness = random.uniform(0.3, 1.2)
            
            # Randomize Color Palette
            num_colors = random.choice([2, 3])
            current_hues = [random.randint(0, 180) for _ in range(num_colors)]
            
            # Randomize Background Color
            bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            
            # Update Spiral Transformer
            self.spiral_transformer.tightness = spiral_tightness

            # 1. Vector Creation
            current_scale = random.uniform(0.5, 0.8)
            points = self._generate_initial_triangle(current_scale)

            # 2. Apply Koch Recursion (Linear Transform)
            for _ in range(num_transforms):
                points = self.koch_transformer.apply({}, points) # type: ignore
                
            # 3. Apply Spiral Twist (Linear Transform)
            points = self.spiral_transformer.apply({}, points) # type: ignore

            # 4. Rasterize (Draw to pixels)
            # Draw in White/Gray on Black to provide the base mask
            img = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            poly_coords = [tuple(p) for p in points]
            
            draw.polygon(poly_coords, fill=(255, 255, 255), outline=(128, 128, 128))

            # 5. Apply Psychedelic Mask with Random Hues and Background
            img = self._apply_psychedelic_mask(img, current_hues, bg_color)

            # 6. Save
            if self.file_count == 1:
                filename = f"{output_dir}/{self.base_filename}.jpg"
            else:
                filename = f"{output_dir}/{self.base_filename}_{i+1}.jpg"
            
            self.save(img, filename)
            
            hue_str = ">".join(map(str, current_hues))
            log.info(f"Generated: {filename} (Iter: {num_transforms}, Spiral: {spiral_tightness:.2f}, Hues: {hue_str}, BG: {bg_color})")
