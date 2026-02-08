import numpy as np # type: ignore
import random
import colorsys
from PIL import Image, ImageDraw # type: ignore
from . import drawInputSource
from .. import common
from .. import log

class Bubbles(drawInputSource.DrawInputSource):
    def __init__(self, config: dict | None):
        super().__init__()
        self.config = config if config else {}
        
        # Standard Configuration
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        self.file_count = 10 ## int(self.config.get('file_count', 1))
        
        # Bubbles Specific
        self.min_radius = int(self.config.get('min_radius', 10))
        self.max_radius = int(self.config.get('max_radius', 60))
        self.base_filename = "bubbles"

        # --- MODES ---
        # 1. radial_flip: Center Hue -> Opposite Edge Hue (180 deg shift)
        # 2. radial_rainbow: Center Hue -> Cycle 360 -> Center Hue at Edge
        self.math_modes = ['random', 'radial_flip', 'radial_rainbow']
        
        # Themes (User restricted to Fire only)
        self.theme_modes = ['fire']
        
        self.all_modes = self.math_modes + self.theme_modes

    def get_color(self, mode, norm_dist, base_hue, jitter, s_rnd, v_rnd):
        """
        Calculates color based on mode and pre-calculated randoms.
        """
        h, s, v = 0.0, 0.0, 0.0
        
        # --- MATH MODES ---
        if mode == 'radial_flip':
            # Start at base, shift exactly 0.5 (180 deg) by the edge
            h = (base_hue + (norm_dist * 0.5)) % 1.0
            s = 0.8 + s_rnd
            v = 0.9 + v_rnd
            
        elif mode == 'radial_rainbow':
            # Start at base, shift exactly 1.0 (360 deg) by the edge
            # Removed hue jitter so the edge color matches center color perfectly
            h = (base_hue + norm_dist) % 1.0
            s = 0.8 + s_rnd
            v = 0.9 + v_rnd
            
        elif mode == 'random':
            # This case is usually handled by the vectorized block in draw_bubbles,
            # but kept here as fallback if needed.
            h = jitter # Jitter is random 0-1 in this context? No, handled outside.
            pass 

        # --- THEMED PALETTES ---
        elif mode == 'fire':
            # Red/Orange/Yellow range (0.0 to 0.15)
            # Map jitter (-0.05 to 0.05) to a larger positive range
            h = 0.0 + (abs(jitter) * 1.5) 
            if h > 0.15: h = 0.15
            s = 0.8 + abs(s_rnd)
            v = 0.8 + abs(v_rnd)

        # Safety clamps for Saturation/Value
        s = max(0.0, min(1.0, s))
        v = max(0.0, min(1.0, v))
        
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

    def draw_bubbles(self, draw, width, height, add_highlights=False):
        # 1. Randomize Count
        count = random.randint(50, 5000)
        cx, cy = width / 2, height / 2
        
        # 2. Numpy Optimization: Vectorized Coordinates & Radii
        x = np.random.uniform(0, width, count)
        y = np.random.uniform(0, height, count)
        
        dist_x = x - cx
        dist_y = y - cy
        distances = np.sqrt(dist_x**2 + dist_y**2)
        
        max_dist = np.sqrt(cx**2 + cy**2)
        if max_dist == 0: max_dist = 1
        norm_dist = distances / max_dist
        
        base_r = self.max_radius - (self.max_radius - self.min_radius) * norm_dist
        variance_r = np.random.uniform(0.75, 1.25, count)
        final_r = base_r * variance_r

        # 3. Determine Mode
        mode = random.choice(self.all_modes)
        base_hue = random.random()
        colors = []

        # 4. Color Generation (Optimized Randoms)
        if mode == 'random':
            # Ultra-fast path for pure random
            colors = np.random.randint(0, 256, (count, 3))
            colors = [tuple(c) for c in colors]
        else:
            # Vectorized randoms for complex logic
            # Jitter: -0.05 to 0.05
            jitters = np.random.uniform(-0.05, 0.05, count)
            # Sat/Val variance: -0.1 to 0.1
            s_rnds = np.random.uniform(-0.1, 0.1, count)
            v_rnds = np.random.uniform(-0.1, 0.1, count)
            
            # Build list
            for d, j, s, v in zip(norm_dist, jitters, s_rnds, v_rnds):
                colors.append(self.get_color(mode, d, base_hue, j, s, v))

        # 5. Drawing Loop
        for xi, yi, ri, color in zip(x, y, final_r, colors):
            xi, yi, ri = int(xi), int(yi), int(ri)
            if ri < 1: ri = 1
            
            # Draw Bubble
            draw.ellipse(
                (xi - ri, yi - ri, xi + ri, yi + ri), 
                fill=color, 
                outline=None 
            )
            
            # Draw Highlight
            if add_highlights:
                high_r = int(ri * 0.25)
                if high_r < 1: high_r = 1
                
                offset = int(ri * 0.35)
                h_x = xi - offset
                h_y = yi - offset
                
                draw.ellipse(
                    (h_x - high_r, h_y - high_r, h_x + high_r, h_y + high_r),
                    fill="white",
                    outline=None
                )
        
        log.info(f"Generated: {count} bubbles. Mode: {mode}. Highlights: {add_highlights}")

    def draw(self):
        for i in range(self.file_count):
            img = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # 50% chance for highlights
            has_reflection = random.choice([True, False])
            
            self.draw_bubbles(draw, self.width, self.height, add_highlights=has_reflection)

            filename = f"{common.INPUT_SOURCES_IN}/Bubbles/{self.base_filename}{i+1}.jpeg"
            img.save(filename, 'JPEG')
            log.info(f"Saved: {filename}")
