from .base import RasterTransformer
import numpy as np # type: ignore
import random
from PIL import Image, ImageOps # type: ignore

class FlipWilsonTransformer(RasterTransformer):
    """
    Reflects a specific half (or corner) of an image onto the rest,
    applying a perspective warp (trapezoid effect) to the reflection.
    """
    
    def __init__(self, keep: str | None = None):
        super().__init__() # Initialize base first to setup metadata_dictionary

        keep_options = [
            'left', 'right', 'top', 'bottom',
            'top_left', 'top_right', 'bottom_left', 'bottom_right']
        self.keep = keep or random.choice(keep_options)
        
        # --- GENERATE PARAMETERS IN INIT ---
        # We define them here so the metadata is ready immediately for filenames
        self.narrow_factor = random.uniform(0.2, 0.5)

        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "keep": self.keep,
            "narrow": round(self.narrow_factor, 2)
        }
        # -------------------------

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        if isinstance(img_np, np.ndarray):
            img = Image.fromarray(img_np)
        elif isinstance(img_np, Image.Image):
            img = img_np.copy()
        else:
            return img_np

        # Use the pre-calculated parameters
        if self.keep == "left":
            self._reflect_horizontal(img, keep_left=True)
        elif self.keep == "right":
            self._reflect_horizontal(img, keep_left=False)
        elif self.keep == "top":
            self._reflect_vertical(img, keep_top=True)
        elif self.keep == "bottom":
            self._reflect_vertical(img, keep_top=False)
        elif self.keep == "top_left":
            self._reflect_vertical(img, keep_top=True)
            self._reflect_horizontal(img, keep_left=True)
        elif self.keep == "top_right":
            self._reflect_vertical(img, keep_top=True)
            self._reflect_horizontal(img, keep_left=False)
        elif self.keep == "bottom_left":
            self._reflect_vertical(img, keep_top=False)
            self._reflect_horizontal(img, keep_left=True)
        elif self.keep == "bottom_right":
            self._reflect_vertical(img, keep_top=False)
            self._reflect_horizontal(img, keep_left=False)

        return np.array(img)

    def _reflect_horizontal(self, img: Image.Image, keep_left: bool) -> None:
        w, h = img.size
        mid = w // 2
        
        if keep_left:
            source = img.crop((0, 0, mid, h))
            mirror = ImageOps.mirror(source)
            mirror = self._warp_trapezoid(mirror, narrow_side='right')
            img.paste(mirror, (mid, 0), mirror)
        else:
            source = img.crop((mid, 0, w, h))
            mirror = ImageOps.mirror(source)
            mirror = self._warp_trapezoid(mirror, narrow_side='left')
            img.paste(mirror, (0, 0), mirror)

    def _reflect_vertical(self, img: Image.Image, keep_top: bool) -> None:
        w, h = img.size
        mid = h // 2
        
        if keep_top:
            source = img.crop((0, 0, w, mid))
            flip = ImageOps.flip(source)
            flip = self._warp_trapezoid(flip, narrow_side='bottom')
            img.paste(flip, (0, mid), flip)
        else:
            source = img.crop((0, mid, w, h))
            flip = ImageOps.flip(source)
            flip = self._warp_trapezoid(flip, narrow_side='top')
            img.paste(flip, (0, 0), flip)

    def _warp_trapezoid(self, img: Image.Image, narrow_side: str) -> Image.Image:
        w, h = img.size
        img = img.convert("RGBA")
        
        # Use the stored narrow_factor
        dx = int((w * self.narrow_factor) / 2)
        dy = int((h * self.narrow_factor) / 2)
        
        if narrow_side == 'top':
            dest_corners = [(dx, 0), (w - dx, 0), (w, h), (0, h)]
        elif narrow_side == 'bottom':
            dest_corners = [(0, 0), (w, 0), (w - dx, h), (dx, h)]
        elif narrow_side == 'left':
            dest_corners = [(0, dy), (w, 0), (w, h), (0, h - dy)]
        elif narrow_side == 'right':
            dest_corners = [(0, 0), (w, dy), (w, h - dy), (0, h)]
        else:
            return img

        src_corners = [(0, 0), (w, 0), (w, h), (0, h)]
        coeffs = self._find_coeffs(dest_corners, src_corners)
        
        return img.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)

    def _find_coeffs(self, pa, pb):
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
        A = np.matrix(matrix, dtype=np.float32)
        B = np.array(pb).reshape(8)
        res = np.linalg.solve(A, B)
        return np.array(res).reshape(8)
