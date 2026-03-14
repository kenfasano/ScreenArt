import numpy as np
import cv2
import random
from .rasterTransformer import RasterTransformer


class KaleidoscopeTransformer(RasterTransformer):
    """
    Creates a kaleidoscope effect by mirroring one wedge of the image
    around the centre point repeatedly. The number of segments controls
    how many mirror repetitions fill the circle.
    Spectacular on bubbles, cubes, and peripheral_drift.
    """

    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("kaleidoscopetransformer", {})

        # Number of mirror segments (must be even; 4/6/8/12 work best)
        segments = t_config.get("segments")
        if not isinstance(segments, int):
            segments = random.choice([4, 6, 8, 8, 12])

        # Centre offset from image centre as fraction [-0.3, 0.3]
        cx_offset = t_config.get("cx_offset")
        cy_offset = t_config.get("cy_offset")
        if not isinstance(cx_offset, (int, float)):
            cx_offset = random.uniform(-0.2, 0.2)
        if not isinstance(cy_offset, (int, float)):
            cy_offset = random.uniform(-0.2, 0.2)

        self.metadata_dictionary["segments"] = segments
        self.metadata_dictionary["cx_off"]   = round(float(cx_offset), 2)
        self.metadata_dictionary["cy_off"]   = round(float(cy_offset), 2)

        img = self.to_uint8(img_np)
        h, w = img.shape[:2]

        cx = w / 2.0 + cx_offset * w
        cy = h / 2.0 + cy_offset * h

        # Build polar coordinate maps
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        dx = xx - cx
        dy = yy - cy

        r     = np.sqrt(dx * dx + dy * dy)
        theta = np.arctan2(dy, dx)  # [-π, π]

        # Fold theta into [0, 2π/segments] wedge, then mirror
        wedge = 2.0 * np.pi / segments
        # Normalise to [0, 2π)
        theta_pos = theta % (2.0 * np.pi)
        # Map to [0, wedge)
        theta_fold = theta_pos % wedge
        # Mirror within wedge
        half = wedge / 2.0
        theta_mirror = np.where(theta_fold <= half, theta_fold, wedge - theta_fold)

        # Convert back to Cartesian source coords
        src_x = (cx + r * np.cos(theta_mirror)).astype(np.float32)
        src_y = (cy + r * np.sin(theta_mirror)).astype(np.float32)

        out = cv2.remap(img, src_x, src_y, cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REFLECT_101)
        return self.to_float32(out)
