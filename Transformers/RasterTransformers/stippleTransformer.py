import numpy as np
import cv2
import random
from .rasterTransformer import RasterTransformer


class StippleTransformer(RasterTransformer):
    """
    Converts the image to a dot/stipple pattern weighted by local brightness.
    Darker areas get more densely packed dots; bright areas are sparse.
    Each dot takes the colour of its source pixel.
    Produces a distinctive pointillist / screen-print aesthetic.
    """

    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("stippletransformer", {})

        # Dot radius in pixels
        dot_radius = t_config.get("dot_radius")
        if not isinstance(dot_radius, int):
            dot_radius = random.randint(2, 6)

        # Grid spacing: distance between dot centres
        spacing = t_config.get("spacing")
        if not isinstance(spacing, int):
            spacing = random.randint(dot_radius * 2, dot_radius * 4)

        # Background colour: "white", "black", or "complement"
        bg = t_config.get("background")
        if not isinstance(bg, str) or bg not in ("white", "black", "complement"):
            bg = random.choice(("white", "black", "complement"))

        # Jitter: randomly offset each dot centre slightly
        jitter = t_config.get("jitter", True)
        if isinstance(jitter, str):
            jitter = True

        self.metadata_dictionary["dot_radius"] = dot_radius
        self.metadata_dictionary["spacing"]    = spacing
        self.metadata_dictionary["bg"]         = bg
        self.metadata_dictionary["jitter"]     = int(jitter)

        img = self.to_uint8(img_np)
        h, w = img.shape[:2]

        # Background canvas
        if bg == "white":
            canvas = np.full_like(img, 255)
        elif bg == "black":
            canvas = np.zeros_like(img)
        else:  # complement: invert the image as background
            canvas = (255 - img)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

        half = spacing // 2
        for y in range(half, h - half, spacing):
            for x in range(half, w - half, spacing):
                # Brightness at this grid point (inverted: dark = big dot)
                brightness = float(gray[y, x])
                # Dot size scales inversely with brightness
                r = max(1, int(dot_radius * (1.0 - brightness * 0.7)))

                if jitter:
                    jx = random.randint(-half // 2, half // 2)
                    jy = random.randint(-half // 2, half // 2)
                    px = max(0, min(w - 1, x + jx))
                    py = max(0, min(h - 1, y + jy))
                else:
                    px, py = x, y

                colour = img[py, px].tolist()
                cv2.circle(canvas, (px, py), r, colour, -1, cv2.LINE_AA)

        return self.to_float32(canvas)
