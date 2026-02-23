import os
import numpy as np
import random
import colorsys
from PIL import Image, ImageDraw
from .drawGenerator import DrawGenerator

class Bubbles(DrawGenerator):
    def __init__(self):
        super().__init__()
        
        # Standard Configuration
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = 10 
        
        # Bubbles Specific
        self.min_radius = int(self.config.get('min_radius', 10))
        self.max_radius = int(self.config.get('max_radius', 60))
        self.base_filename = "bubbles"

        self.math_modes = ['random', 'radial_flip', 'radial_rainbow']
        self.theme_modes = ['fire']
        self.all_modes = self.math_modes + self.theme_modes

    def get_color(self, mode, norm_dist, base_hue, jitter, s_rnd, v_rnd):
        h, s, v = 0.0, 0.0, 0.0
        
        if mode == 'radial_flip':
            h = (base_hue + (norm_dist * 0.5)) % 1.0
            s = 0.8 + s_rnd
            v = 0.9 + v_rnd
        elif mode == 'radial_rainbow':
            h = (base_hue + norm_dist) % 1.0
            s = 0.8 + s_rnd
            v = 0.9 + v_rnd
        elif mode == 'random':
            h = jitter 
        elif mode == 'fire':
            h = 0.0 + (abs(jitter) * 1.5) 
            if h > 0.15:
                h = 0.15
            s = 0.8 + abs(s_rnd)
            v = 0.8 + abs(v_rnd)

        s = max(0.0, min(1.0, s))
        v = max(0.0, min(1.0, v))
        
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

    def draw_bubbles(self, draw, width, height, add_highlights=False):
        count = random.randint(50, 5000)
        cx, cy = width / 2, height / 2
        
        x = np.random.uniform(0, width, count)
        y = np.random.uniform(0, height, count)
        
        dist_x = x - cx
        dist_y = y - cy
        distances = np.sqrt(dist_x**2 + dist_y**2)
        
        max_dist = np.sqrt(cx**2 + cy**2)
        if max_dist == 0:
            max_dist = 1
        norm_dist = distances / max_dist
        
        base_r = self.max_radius - (self.max_radius - self.min_radius) * norm_dist
        variance_r = np.random.uniform(0.75, 1.25, count)
        final_r = base_r * variance_r

        mode = random.choice(self.all_modes)
        base_hue = random.random()
        colors = []

        if mode == 'random':
            colors = np.random.randint(0, 256, (count, 3))
            colors = [tuple(c) for c in colors]
        else:
            jitters = np.random.uniform(-0.05, 0.05, count)
            s_rnds = np.random.uniform(-0.1, 0.1, count)
            v_rnds = np.random.uniform(-0.1, 0.1, count)
            
            for d, j, s, v in zip(norm_dist, jitters, s_rnds, v_rnds):
                colors.append(self.get_color(mode, d, base_hue, j, s, v))

        for xi, yi, ri, color in zip(x, y, final_r, colors):
            xi, yi, ri = int(xi), int(yi), int(ri)
            if ri < 1: ri = 1
            
            draw.ellipse((xi - ri, yi - ri, xi + ri, yi + ri), fill=color, outline=None)
            
            if add_highlights:
                high_r = max(1, int(ri * 0.25))
                offset = int(ri * 0.35)
                h_x, h_y = xi - offset, yi - offset
                draw.ellipse((h_x - high_r, h_y - high_r, h_x + high_r, h_y + high_r), fill="white", outline=None)
        
        self.log.info(f"Generated: {count} bubbles. Mode: {mode}. Highlights: {add_highlights}")

    def run(self, *args, **kwargs): # type: ignore
        out_dir = os.path.join(self.config["paths"
                                           ]["generators_in"], "bubbles")
        os.makedirs(out_dir, exist_ok=True)

        for i in range(self.file_count):
            img = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            has_reflection = random.choice([True, False])
            self.draw_bubbles(draw, self.width, self.height, add_highlights=has_reflection)

            filename = os.path.join(out_dir, f"{self.base_filename}_{i+1}.jpeg")
            try:
                img.save(filename)
            except Exception as e:
                self.log.error(f"Failed to save {filename}: {e}")
