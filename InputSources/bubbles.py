import numpy as np
import random
import threading
from . import drawInputSource
from .. import common
from .. import log
from PIL import Image, ImageDraw
from typing import Any

DEFAULT_FILE_COUNT = 3

#An image with bubbles that are all the same color: my_bubbles.draw(filename="blue_bubbles.jpeg", color=(0, 0, 255))
#
#An image with large bubbles in a random color range: my_bubbles.draw(filename="large_bubbles.jpeg", radius=[10, 20])

class Bubbles(drawInputSource.DrawInputSource):
    def __init__(self, config: dict | None):
        super().__init__()
        self.config = config.get("bubbles", None) if config else None

    def random_rgb(self) -> tuple[int, int, int]:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        color = (r, g, b)
        return color

    def parse_arg(self, key: str, default: Any) -> Any:
        result = default

        if self.config:
            value = self.config.get(key, None)

            if value:
                if isinstance(value, list): 
                    if len(value) == 3:
                        result = tuple(value)
                    elif len(value) == 2:
                        result = random.randint(value[0], value[1])
                else:
                    result = value
            else:
                result = default

            return result 

    def configure(self):
        if not self.config:
            raise ValueError("No config for bubbles!")

        self.count = self.config.get("count", 10000)
        self.iterations = self.config.get("iterations", 4)

        self.file_count = self.config.get("file_count", DEFAULT_FILE_COUNT) if self.config else DEFAULT_FILE_COUNT
        self.base_filename = "bubbles"

        self.radius = self.parse_arg("radius", random.randint(20, 1000))
        self.fill_color = self.parse_arg("fill_color", self.random_rgb())
        self.outline_color = self.parse_arg("outline_color", self.random_rgb())
        self.bg_color = self.parse_arg("bg_color", "white")
        self.width = self.parse_arg("width", random.randint(200, 1200))
        self.height = self.parse_arg("height", random.randint(120, 800))
        
        # New: Factor to multiply radius by at the center (default 1.0 = no change)
        self.center_radius_multiplier = float(self.parse_arg("center_radius_multiplier", 1.0))
        
        # New: Pre-calculate center and max distance (corner to center) for performance
        self.cx = self.width / 2
        self.cy = self.height / 2
        # Pythagorean theorem to find distance from center to corner
        self.max_dist = (self.cx**2 + self.cy**2) ** 0.5

    def draw_bubbles(self, 
                     image_draw: ImageDraw.ImageDraw, 
                     x_coords: np.ndarray, y_coords: np.ndarray, 
                     start_index: int, lock: threading.Lock):
        try:
            # Iterate through the specified range of bubbles
            for i in range(start_index, self.count, 2):
                x = int(x_coords[i])
                y = int(y_coords[i])

                # Determine bubble radius (Base calculation)
                if isinstance(self.radius, (int, float)):
                    radius = int(self.radius)
                elif isinstance(self.radius, tuple) and len(self.radius) == 2:
                    min_radius, max_radius = self.radius
                    radius = random.randint(min_radius, max_radius)
                else:
                    radius = random.randint(1, 5)

                # --- NEW LOGIC START ---
                # Apply radial scaling if the multiplier is active (> 1.0)
                if self.center_radius_multiplier > 1.0:
                    # Calculate distance from center
                    dist = ((x - self.cx)**2 + (y - self.cy)**2) ** 0.5
                    
                    # Normalize distance: 0.0 at center, 1.0 at corner
                    norm_dist = dist / self.max_dist
                    
                    # Linear interpolation:
                    # Multiplier starts at 'center_radius_multiplier' and decays to 1.0 at edge
                    scale_factor = self.center_radius_multiplier - (self.center_radius_multiplier - 1.0) * norm_dist
                    
                    # Apply scale
                    radius = int(radius * scale_factor)
                # --- NEW LOGIC END ---

                # Determine bubble color
                fill_color = self.fill_color or self.random_rgb()
                outline_color = self.outline_color or self.random_rgb()

                # Ensure coordinates are within image bounds
                if 0 <= x < self.width and 0 <= y < self.height:
                    # Use a lock to ensure thread safety when drawing on the shared object
                    with lock:
                        image_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill_color, outline=outline_color)
        except Exception as e:
            log.critical(str(e))
            print(str(e))

    def draw_default_bell_curve(self, draw: ImageDraw.ImageDraw):
        """
        Draws colored bubbles on the provided ImageDraw object using a bell curve distribution
        and a two-threaded approach for performance.
        """

        # Generate all x and y coordinates from a normal (bell curve) distribution
        x_coords = np.random.normal(loc=self.width/2, scale=self.width/6, size=self.count)
        y_coords = np.random.normal(loc=self.height/2, scale=self.height/6, size=self.count)

        # Create a lock to synchronize access to the ImageDraw object
        lock = threading.Lock()

        # Create and start two threads, one for even indices and one for odd indices

        thread1 = threading.Thread(target=self.draw_bubbles, 
                                   args=(draw, x_coords, y_coords, 0, lock))
        thread2 = threading.Thread(target=self.draw_bubbles, 
                                   args=(draw, x_coords, y_coords, 1, lock))
        thread1.start()
        thread2.start()

        # Wait for both threads to complete their execution
        thread1.join()
        thread2.join()

    def draw(self):
        """
        Creates an image with a bell curve distribution of colored bubbles and saves it as a JPEG.
        """
        self.configure()

        for i in range(self.file_count):
            bg_color = self.random_rgb() if self.bg_color == "random" else self.bg_color
            # Create a new blank white image
            img = Image.new('RGB', (self.width, self.height), bg_color)
            drawing = ImageDraw.Draw(img)

            # Call the new helper method to draw the bubbles
            self.draw_default_bell_curve(drawing)

            # Save the image as a JPEG file
            this_filename: str = f"{common.INPUT_SOURCES_IN}/Bubbles/{self.base_filename}{i+1}.jpeg"
            img.save(this_filename, 'JPEG')
