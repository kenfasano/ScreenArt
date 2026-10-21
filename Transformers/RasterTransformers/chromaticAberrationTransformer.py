import numpy as np
import cv2
import random
from .rasterTransformer import RasterTransformer


class ChromaticAberrationTransformer(RasterTransformer):
    """
    Simulates lens chromatic aberration by shifting the R and B channels
    in opposite directions while leaving G in place.
    Produces a subtle RGB fringe/glitch effect at edges — works especially
    well on space images, bubbles, and high-contrast subjects.
    """

    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("chromaticaberrationtransformer", {})

        # Shift magnitude in pixels (float → subpixel via remap)
        shift = t_config.get("shift")
        if not isinstance(shift, (int, float)):
            shift = random.uniform(4.0, 18.0)
        shift = float(shift)

        # Angle of the shift axis in degrees (0=horizontal, 90=vertical)
        angle = t_config.get("angle")
        if not isinstance(angle, (int, float)):
            angle = random.uniform(0.0, 360.0)
        angle_rad = float(angle) * np.pi / 180.0

        # Edge fade: blend aberration to zero toward image centre so it looks lens-like
        edge_fade = t_config.get("edge_fade", True)
        if isinstance(edge_fade, str):
            edge_fade = True

        self.metadata_dictionary["shift"] = round(shift, 1)
        self.metadata_dictionary["angle"] = round(float(angle), 1)
        self.metadata_dictionary["edge_fade"] = int(edge_fade)

        img = self.to_uint8(img_np)   # uint8 BGR
        h, w = img.shape[:2]

        dx = shift * np.cos(angle_rad)
        dy = shift * np.sin(angle_rad)

        # Build remap grids for R (+shift) and B (-shift), G stays put
        base_x, base_y = np.meshgrid(np.arange(w, dtype=np.float32),
                                     np.arange(h, dtype=np.float32))

        if edge_fade:
            # Radial weight: 0 at centre, 1 at corners
            cx, cy = w / 2.0, h / 2.0
            dist = np.sqrt(((base_x - cx) / cx) ** 2 + ((base_y - cy) / cy) ** 2)
            weight = np.clip(dist, 0.0, 1.0).astype(np.float32)
        else:
            weight = np.ones((h, w), dtype=np.float32)

        map_r_x = (base_x + dx * weight).astype(np.float32)
        map_r_y = (base_y + dy * weight).astype(np.float32)
        map_b_x = (base_x - dx * weight).astype(np.float32)
        map_b_y = (base_y - dy * weight).astype(np.float32)

        b, g, r = cv2.split(img)

        r_shifted = cv2.remap(r, map_r_x, map_r_y, cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT_101)
        b_shifted = cv2.remap(b, map_b_x, map_b_y, cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT_101)

        out = cv2.merge([b_shifted, g, r_shifted])
        return self.to_float32(out)
