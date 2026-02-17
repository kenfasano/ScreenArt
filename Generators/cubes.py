import math
import random
import colorsys
from PIL import Image, ImageDraw, ImageChops # type: ignore
from . import drawGenerator
from .. import common
from .. import log

class Cubes(drawGenerator.DrawGenerator):
    def __init__(self, config: dict) -> None:
        super().__init__(config, "cubes")
        
        # Standard Configuration
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = int(self.config.get('file_count', 6))
        self.base_filename = "cubes"
        
        # Cube Specific Configuration
        self.loops = int(self.config.get('loops', 2000))
        self.min_size = int(self.config.get('min_size', 25))
        self.max_size = int(self.config.get('max_size', 200))

        # --- New Modes ---
        # Adapted from Bubbles concepts for variation
        self.modes = [
            'random',           # Standard vibrant random colors
            'radial_rainbow',   # Hue shifts 360deg from center to edge
            'radial_flip',      # Hue shifts 180deg from center to edge
            'fire',             # Warm palette (reds/oranges)
            'cool',             # Cool palette (blues/cyans/purples)
            'grayscale'         # Monochromatic
        ]

    def _get_rotated_corners(self, cx, cy, size, angle_rad):
        """Calculates the 4 corners of a rotated square."""
        half_size = size / 2
        c = math.cos(angle_rad)
        s = math.sin(angle_rad)
        
        corners_local = [
            (-half_size, -half_size), (half_size, -half_size),
            (half_size, half_size), (-half_size, half_size)
        ]
        
        rotated_points = []
        for x, y in corners_local:
            xr = x * c - y * s
            yr = x * s + y * c
            rotated_points.append((cx + xr, cy + yr))
            
        return rotated_points

    def get_color(self, mode, norm_dist, base_hue):
        """
        Calculates rgb tuple based on mode, distance from center, and a base hue.
        Logic adapted from Bubbles get_color to work in iterative loop.
        """
        h, s, v = 0.0, 0.0, 0.0
        
        # Default high vibrancy
        s = random.uniform(0.6, 1.0)
        v = random.uniform(0.7, 1.0)

        if mode == 'random':
            h = random.random()
            
        # --- Spatial Modes ---
        elif mode == 'radial_rainbow':
            # Shift hue full 360 (1.0) from center to edge based on base_hue
            h = (base_hue + norm_dist) % 1.0
        elif mode == 'radial_flip':
            # Shift hue 180 (0.5) from center to edge
            h = (base_hue + (norm_dist * 0.5)) % 1.0

        # --- Themed Palettes ---
        elif mode == 'fire':
            # Red/Orange/Yellow range (approx 0.0 to 0.15 hue)
            h = random.uniform(0.98, 1.15) % 1.0 # Wrap around 0 for reds
            s = random.uniform(0.8, 1.0) # Higher saturation for fire
        elif mode == 'cool':
             # Cyan/Blue/Purple range (approx 0.5 to 0.85 hue)
            h = random.uniform(0.5, 0.85)
        elif mode == 'grayscale':
            s = 0.0
            v = random.uniform(0.2, 0.95)

        # Ensure standard saturation/value constraints apply to spatial modes
        if mode not in ['grayscale', 'fire']:
             s = max(0.5, min(1.0, s))
             v = max(0.6, min(1.0, v))

        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))

    def draw(self) -> None:
        img_cx, img_cy = self.width / 2, self.height / 2
        # Calculate maximum possible distance from center to a corner
        max_dist = math.sqrt(img_cx**2 + img_cy**2) or 1

        for i in range(self.file_count):
            # Select a mode for this image
            mode = random.choice(self.modes)
            # Select a base hue for radial modes
            base_hue = random.random()

            img = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Collision mask
            mask = Image.new('1', (self.width, self.height), 0)
            mask_draw = ImageDraw.Draw(mask)
            
            placed_count = 0
            
            for _ in range(self.loops):
                # 1. Random Parameters
                size = random.randint(self.min_size, self.max_size)
                margin = int(size * 0.75) 
                cx = random.randint(margin, self.width - margin)
                cy = random.randint(margin, self.height - margin)
                angle = random.uniform(0, 2 * math.pi)
                
                # 2. Calculate Geometry
                points = self._get_rotated_corners(cx, cy, size, angle)
                
                # 3. Collision Detection
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                bbox = (int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1)
                bbox = (max(0, bbox[0]), max(0, bbox[1]), min(self.width, bbox[2]), min(self.height, bbox[3]))
                
                if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]: continue
                
                mask_crop = mask.crop(bbox)
                local_points = [(p[0] - bbox[0], p[1] - bbox[1]) for p in points]
                shape_test_img = Image.new('1', (bbox[2] - bbox[0], bbox[3] - bbox[1]), 0)
                ImageDraw.Draw(shape_test_img).polygon(local_points, fill=1)
                
                if ImageChops.logical_and(mask_crop, shape_test_img).getbbox():
                    continue
                
                # 4. Success - Draw
                # Calculate normalized distance for spatial coloring
                dist = math.sqrt((cx - img_cx)**2 + (cy - img_cy)**2)
                norm_dist = dist / max_dist
                
                color = self.get_color(mode, norm_dist, base_hue)
                
                draw.polygon(points, fill=color, outline=None)
                mask_draw.polygon(points, fill=1)
                placed_count += 1

            filename = f"{self.paths["generators_in"]}/Cubes/{self.base_filename}_{i+1}.jpg"
            self.save(img, filename)
            log.info(f"Saved: {filename}. Mode: {mode}. (Placed {placed_count} cubes)")
