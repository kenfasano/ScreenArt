import math
import random
import colorsys
import os
from PIL import Image, ImageDraw, ImageChops 
from .drawGenerator import DrawGenerator

class Cubes(DrawGenerator):
    def __init__(self):
        super().__init__()
        
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = int(self.config.get('file_count', 6))
        self.base_filename = "cubes"
        
        self.loops = int(self.config.get('loops', 2000))
        self.min_size = int(self.config.get('min_size', 25))
        self.max_size = int(self.config.get('max_size', 200))

        self.modes = [
            'random', 'radial_rainbow', 'radial_flip',
            'fire', 'cool', 'grayscale'
        ]

    def _get_rotated_corners(self, cx, cy, size, angle_rad):
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
        h, s, v = 0.0, random.uniform(0.6, 1.0), random.uniform(0.7, 1.0)

        if mode == 'random':
            h = random.random()
        elif mode == 'radial_rainbow':
            h = (base_hue + norm_dist) % 1.0
        elif mode == 'radial_flip':
            h = (base_hue + (norm_dist * 0.5)) % 1.0
        elif mode == 'fire':
            h = random.uniform(0.98, 1.15) % 1.0 
            s = random.uniform(0.8, 1.0) 
        elif mode == 'cool':
            h = random.uniform(0.5, 0.85)
        elif mode == 'grayscale':
            s = 0.0
            v = random.uniform(0.2, 0.95)

        if mode not in ['grayscale', 'fire']:
             s = max(0.5, min(1.0, s))
             v = max(0.6, min(1.0, v))

        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))

    def run(self, *args, **kwargs) -> None:
        img_cx, img_cy = self.width / 2, self.height / 2
        max_dist = math.sqrt(img_cx**2 + img_cy**2) or 1
        
        out_dir = os.path.join(self.config["paths"]["generators_in"], "cubes")
        os.makedirs(out_dir, exist_ok=True)

        for i in range(self.file_count):
            mode = random.choice(self.modes)
            base_hue = random.random()

            img = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            mask = Image.new('1', (self.width, self.height), 0)
            mask_draw = ImageDraw.Draw(mask)
            
            placed_count = 0
            
            for _ in range(self.loops):
                size = random.randint(self.min_size, self.max_size)
                margin = int(size * 0.75) 
                cx = random.randint(margin, self.width - margin)
                cy = random.randint(margin, self.height - margin)
                angle = random.uniform(0, 2 * math.pi)
                
                points = self._get_rotated_corners(cx, cy, size, angle)
                
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
                
                dist = math.sqrt((cx - img_cx)**2 + (cy - img_cy)**2)
                norm_dist = dist / max_dist
                color = self.get_color(mode, norm_dist, base_hue)
                
                draw.polygon(points, fill=color, outline=None)
                mask_draw.polygon(points, fill=1)
                placed_count += 1

            filename = os.path.join(out_dir, f"{self.base_filename}_{i+1}.jpg")
            try:
                img.save(filename)
                self.log.info(f"Saved: {filename}. Mode: {mode}. (Placed {placed_count} cubes)")
            except Exception as e:
                self.log.error(f"Failed to save {filename}: {e}")
