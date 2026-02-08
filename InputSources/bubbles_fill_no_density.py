import numpy as np
import random
import threading
from . import drawInputSource
from .. import common
from .. import log
from PIL import Image, ImageDraw

DEFAULT_FILE_COUNT = 3

class Bubbles(drawInputSource.DrawInputSource):
    def __init__(self, config: dict | None):
        super().__init__()
        # IGNORE CONFIG. HARDCODE EVERYTHING.
        self.config = {} 
        self.safe_width = 1920
        self.safe_height = 1080
        self.count = 50000

    def configure(self):
        # Double check hardcoding
        self.safe_width = 1920
        self.safe_height = 1080
        self.file_count = 3
        self.base_filename = "bubbles"
        log.info("NUCLEAR BUBBLES: Hardcoded to 1920x1080. Background should be GREEN.")

    def draw_bubbles_simple(self, draw):
        # Simple uniform scatter
        w = self.safe_width
        h = self.safe_height
        
        # Generate x,y across the WHOLE screen
        x = np.random.uniform(0, w, self.count)
        y = np.random.uniform(0, h, self.count)
        r = np.random.randint(20, 50, self.count)
        
        # Random Colors
        colors = np.random.randint(0, 256, (self.count, 3))
        
        for i in range(len(x)):
            xi, yi, ri = int(x[i]), int(y[i]), int(r[i])
            draw.ellipse((xi-ri, yi-ri, xi+ri, yi+ri), fill=tuple(colors[i]), outline="black")

    def draw(self):
        self.configure()
        
        for i in range(self.file_count):
            # FORCE GREEN BACKGROUND
            img = Image.new('RGB', (1920, 1080), (0, 255, 0))
            draw = ImageDraw.Draw(img)
            
            # DRAW GIANT RED X (To prove canvas size)
            draw.line((0, 0, 1920, 1080), fill="red", width=10)
            draw.line((0, 1080, 1920, 0), fill="red", width=10)
            
            # Draw Bubbles
            self.draw_bubbles_simple(draw)

            filename = f"{common.INPUT_SOURCES_IN}/Bubbles/{self.base_filename}{i+1}.jpeg"
            img.save(filename, 'JPEG')
            log.info(f"Saved Nuclear Bubble Image: {filename}")
