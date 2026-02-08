import os
import shutil
from PIL import Image, ImageDraw # type: ignore
from . import drawInputSource
from .. import common
from .. import log

class Hilbert(drawInputSource.DrawInputSource):
    def __init__(self, config: dict, order=5, stroke_width=2, color=(255, 255, 255), bg_color=(0, 0, 0)):
        super().__init__()

        self.config = (config.get("hilbert") if config else {}) or {}
        
        self.width = int(self.config.get('width', 1920))
        self.height = int(self.config.get('height', 1080))
        
        # This explains why you get 40 files (it's in your default.trans)
        self.file_count = int(self.config.get('file_count', 5)) 
        
        self.base_filename = "hilbert"

        # Allow config to override order/stroke if present, otherwise use args
        self.order = int(self.config.get("order", order))
        self.stroke_width = int(self.config.get("stroke_width", stroke_width))
        self.color = color
        self.bg_color = bg_color
        
        # Internal state
        self.points = []
        self.x = 0
        self.y = 0
        self.direction = 0 

    def draw(self):
        width = self.width
        height = self.height
        
        # FIX 1: Correct output directory
        output_dir = f"{common.INPUT_SOURCES_IN}/Hilbert"

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        for i in range(self.file_count):
            log.info(f"Generating Hilbert {i+1}/{self.file_count} (Order {self.order})")
            
            # 1. Generate the normalized points (0.0 to 1.0)
            self._generate_points()

            # 2. Create the image and draw context
            img = Image.new('RGB', (width, height), self.bg_color)
            draw_ctx = ImageDraw.Draw(img)

            # 3. Scale logic (Preserve Aspect Ratio)
            scale_size = min(width, height) * 0.9 # 0.9 margin
            offset_x = (width - scale_size) / 2
            offset_y = (height - scale_size) / 2

            scaled_points = []
            for nx, ny in self.points:
                sx = offset_x + (nx * scale_size)
                sy = offset_y + (ny * scale_size)
                scaled_points.append((sx, sy))

            # 4. Draw the lines
            if len(scaled_points) > 1:
                draw_ctx.line(scaled_points, fill=self.color, width=self.stroke_width)

            # 5. Save
            if self.file_count == 1:
                filename = f"{output_dir}/{self.base_filename}.jpg"
            else:
                filename = f"{output_dir}/{self.base_filename}_{i+1}.jpg"
            
            img.save(filename, 'JPEG')

    def _generate_points(self):
        self.points = []
        self.x, self.y = 0, 0
        self.direction = 0
        
        # Start recursion
        self.points.append((0, 0))
        self._hilbert_a(self.order)
        
        # FIX 2: Dynamic Normalization
        # Instead of assuming 0 to N, we find the actual bounds.
        # This prevents the "drawing off screen" issue if the curve goes negative.
        if not self.points: return

        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        range_x = max(1, max_x - min_x)
        range_y = max(1, max_y - min_y)
        
        # Normalize to 0.0 - 1.0 range based on the bounding box of the curve
        normalized = []
        for px, py in self.points:
            nx = (px - min_x) / range_x
            ny = (py - min_y) / range_y
            normalized.append((nx, ny))
            
        self.points = normalized

    def _move(self, direction):
        if direction == 0:   self.x += 1 # Right
        elif direction == 1: self.y += 1 # Down
        elif direction == 2: self.x -= 1 # Left
        elif direction == 3: self.y -= 1 # Up
        self.points.append((self.x, self.y))

    def _hilbert_a(self, depth):
        if depth <= 0: return
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
        if depth <= 0: return
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
