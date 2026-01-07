import os
import shutil
import random
import colorsys
import numpy as np # type: ignore
from PIL import Image, ImageDraw # type: ignore

from . import drawGenerator
from .. import common
from .. import log

# Import Linear Transformers
try:
    from Transformers.LinearTransformers.kochSnowflakeTransformer import KochSnowflakeTransformer
    from Transformers.LinearTransformers.spiralTransformer import SpiralTransformer
    from Transformers.LinearTransformers.smoothingTransformer import SmoothingTransformer
    from Transformers.LinearTransformers.sinewaveTransformer import SineWaveTransformer
    from Transformers.LinearTransformers.jitterTransformer import JitterTransformer
except ImportError:
    from ..Transformers.LinearTransformers.kochSnowflakeTransformer import KochSnowflakeTransformer
    from ..Transformers.LinearTransformers.spiralTransformer import SpiralTransformer
    from ..Transformers.LinearTransformers.smoothingTransformer import SmoothingTransformer
    from ..Transformers.LinearTransformers.sinewaveTransformer import SineWaveTransformer
    from ..Transformers.LinearTransformers.jitterTransformer import JitterTransformer

class Hilbert(drawGenerator.DrawGenerator):
    def __init__(self, config: dict):
        super().__init__()

        self.config = common.get_config(config, "hilbert")
        
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = int(self.config.get('file_count', 5))
        self.base_filename = "hilbert"

        # Randomize Configuration
        self.order = int(self.config.get("order", random.randint(4, 7)))
        self.stroke_width = int(self.config.get("stroke_width", random.randint(2, 4)))

        # Default colors (overwritten in draw)
        self.bg_color = (0, 0, 0)
        self.points = []

    def _generate_high_contrast_bg(self):
        """Generates a background color and a 'mode' for the gradient."""
        mode = random.choice(["dark", "dark", "light"]) 
        hue = random.random()
        
        if mode == "dark":
            # Dark Background
            bg_r, bg_g, bg_b = colorsys.hsv_to_rgb(hue, 0.3, 0.1)
        else:
            # Light Background
            bg_r, bg_g, bg_b = colorsys.hsv_to_rgb(hue, 0.1, 0.98)

        bg_rgb = (int(bg_r*255), int(bg_g*255), int(bg_b*255))
        return bg_rgb, mode

    def _get_gradient_color(self, x, y, width, height, mode):
        """Calculates RGB color based on X,Y position."""
        # Normalize position 0..1
        nx = x / width
        ny = y / height
        
        # Create a hue based on position (Diagonal gradient)
        # We multiply by 1.0 or 2.0 to decide how many 'rainbows' fit on screen
        hue = (nx + ny) * 0.5 
        hue = (hue + random.random()) % 1.0 # Random offset
        
        if mode == "dark":
            # Neon / Bright colors
            sat = 0.9
            val = 1.0
        else:
            # Dark / Ink colors
            sat = 0.9
            val = 0.4
            
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        return (int(r*255), int(g*255), int(b*255))

    def draw(self):
        width = self.width
        height = self.height
        output_dir = f"{common.GENERATORS_IN}/Hilbert"

        def random_bool(): return random.choice([True, False])

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        for i in range(self.file_count):
            self.order = random.randint(4, 6)
            
            # 1. Decide on Background and Mode
            bg_color, mode = self._generate_high_contrast_bg()
            
            # 2. Decide on Logic
            use_gradient = random_bool() # 50% chance for gradient vs solid
            
            # If solid, pick a high contrast color
            solid_color = (255, 255, 255)
            if not use_gradient:
                # Simple complementary logic for solid color
                bg_hue = colorsys.rgb_to_hsv(bg_color[0]/255, bg_color[1]/255, bg_color[2]/255)[0]
                fg_hue = (bg_hue + 0.5) % 1.0
                fg_val = 1.0 if mode == "dark" else 0.2
                fr, fg, fb = colorsys.hsv_to_rgb(fg_hue, 0.9, fg_val)
                solid_color = (int(fr*255), int(fg*255), int(fb*255))

            # Transformers
            use_koch = random_bool()
            use_spiral = random_bool()
            use_smoother = random_bool()
            use_rippler = random_bool()
            use_jitter = random_bool()
            
            log.debug(f"Generating Hilbert {i+1} (Ord:{self.order}, Grad:{use_gradient}, Spiral:{use_spiral}, Koch:{use_koch})")
            
            self._generate_points()
            pts_array = np.array(self.points) * 1000.0
            
            # Apply Transformers
            if use_koch:
                pts_array = KochSnowflakeTransformer().apply({}, pts_array)
            if use_spiral:
                t = SpiralTransformer()
                t.tightness = random.uniform(0.5, 1.5)
                pts_array = t.apply({}, pts_array)
            if use_smoother:
                t = SmoothingTransformer(iterations=random.randint(2,4), tension=random.uniform(0.15,0.35))
                pts_array = t.apply({}, pts_array)
            if use_rippler:
                pts_array = SineWaveTransformer().apply({}, pts_array)
            if use_jitter:
                pts_array = JitterTransformer().apply({}, pts_array)

            # Draw
            img = Image.new('RGB', (width, height), bg_color)
            draw_ctx = ImageDraw.Draw(img)

            if len(pts_array) > 1:
                # Scale logic
                min_x, min_y = np.min(pts_array, axis=0)
                max_x, max_y = np.max(pts_array, axis=0)
                range_x = max(1e-5, max_x - min_x)
                range_y = max(1e-5, max_y - min_y)
                scale_factor = min(width / range_x, height / range_y) * 0.9
                
                dest_cx, dest_cy = width / 2, height / 2
                src_cx = (min_x + max_x) / 2
                src_cy = (min_y + max_y) / 2
                
                # Transform all points to screen space first
                screen_points = []
                for px, py in pts_array:
                    sx = (px - src_cx) * scale_factor + dest_cx
                    sy = (py - src_cy) * scale_factor + dest_cy
                    screen_points.append((sx, sy))

                if use_gradient:
                    # DRAW SEGMENT BY SEGMENT
                    for j in range(len(screen_points) - 1):
                        p1 = screen_points[j]
                        p2 = screen_points[j+1]
                        
                        # Get color based on midpoint of segment
                        mid_x = (p1[0] + p2[0]) / 2
                        mid_y = (p1[1] + p2[1]) / 2
                        
                        seg_color = self._get_gradient_color(mid_x, mid_y, width, height, mode)
                        
                        # Draw segment (width+1 to avoid gaps)
                        draw_ctx.line([p1, p2], fill=seg_color, width=self.stroke_width)
                        
                        # Fix for jagged joints: draw a circle at the joint? 
                        # Or just overlap slightly. For now, simple lines usually suffice for this art style.
                else:
                    # DRAW ALL AT ONCE (Faster, cleaner joints)
                    draw_ctx.line(screen_points, fill=solid_color, width=self.stroke_width)

            filename = f"{output_dir}/{self.base_filename}_{i+1}.jpg" if self.file_count > 1 else f"{output_dir}/{self.base_filename}.jpg"
            img.save(filename, 'JPEG')

    def _generate_points(self):
        self.points = []
        self.x, self.y = 0, 0
        self.direction = 0
        self.points.append((0, 0))
        self._hilbert_a(self.order)
        
        if not self.points:
            return
        
        # Normalize 0..1
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        range_x = max(1, max_x - min_x)
        range_y = max(1, max_y - min_y)
        
        self.points = [((p[0] - min_x) / range_x, (p[1] - min_y) / range_y) for p in self.points]

    # Recursive Hilbert functions remain unchanged
    def _move(self, direction):
        if direction == 0:
            self.x += 1 
        elif direction == 1:
            self.y += 1 
        elif direction == 2:
            self.x -= 1 
        elif direction == 3:
            self.y -= 1 
        self.points.append((self.x, self.y))

    def _hilbert_a(self, depth):
        if depth <= 0:
            return
        self.direction = (self.direction - 1) % 4 
        self._hilbert_b(depth - 1)                
        self._move(self.direction)                
        self.direction = (self.direction + 1) % 4 
        self._hilbert_a(depth - 1)                
        self._move(self.direction)                
        self._hilbert_a(depth - 1)                
        self.direction = (self.direction + 1) % 4 
        self._move(self.direction)                
        self._hilbert_b(depth - 1)                
        self.direction = (self.direction - 1) % 4 

    def _hilbert_b(self, depth):
        if depth <= 0:
            return
        self.direction = (self.direction + 1) % 4 
        self._hilbert_a(depth - 1)                
        self._move(self.direction)                
        self.direction = (self.direction - 1) % 4 
        self._hilbert_b(depth - 1)                
        self._move(self.direction)                
        self._hilbert_b(depth - 1)                
        self.direction = (self.direction - 1) % 4 
        self._move(self.direction)                
        self._hilbert_a(depth - 1)                
        self.direction = (self.direction + 1) % 4
