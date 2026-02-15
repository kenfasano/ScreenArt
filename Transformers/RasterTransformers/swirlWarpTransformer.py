import cv2 # type: ignore
import numpy as np # type: ignore
from .base import RasterTransformer
from typing import Optional, Tuple

DEFAULT_STRENGTH = 1.25

class SwirlWarpTransformer(RasterTransformer):
    def _compute_falloff(self, r: np.ndarray, R: float) -> np.ndarray:
        if self.falloff == "none":
            f = np.ones_like(r)
        elif self.falloff == "exponential":
            f = np.exp(-r / (R / 3.0 + 1e-6))
        else:
            sigma = R / 2.0 if R > 0 else 1.0
            f = np.exp(-(r ** 2) / (2.0 * sigma ** 2 + 1e-6))
        cutoff = np.exp(-(np.maximum(r - R, 0.0) ** 2) / (2.0 * (0.25 * R + 1e-6) ** 2))
        return f * cutoff

    def __init__(self) -> None:
        super().__init__()

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        import ScreenArt.common as common
        import ScreenArt.log as log

        if img_np is None or img_np.ndim < 2:
            raise ValueError("SwirlWarpTransformer.transform: expected HxW or HxWxC image array")

        self.config = common.get_config(config, "swirlwarptransformer")

        if self.config is None:
            log.error("config is None for SwirlWarpTransformer!")
            return img_np 

        # Note: Preserving possible key typo "self.strength" from original code
        self.strength = self.config.get("self.strength", "?")
        if isinstance(self.strength, float):
            self.strength = self.strength
        else:
            self.strength = DEFAULT_STRENGTH
            
        # --- POPULATE METADATA ---
        self.metadata_dictionary = {
            "strength": self.strength
        }
        # -------------------------

        h, w = img_np.shape[:2]
        self.radius: float = w / 2.0
        self.center: Optional[Tuple[float, float]] = (h / 2.0, w / 2.0) 
        self.band_period: Optional[float] = None
        self.falloff: str = "gaussian"
        cx, cy = (self.center if self.center is not None else (w * 0.5, h * 0.5))
        R = float(self.radius if self.radius not in (None, 0) else min(w, h) * 0.5)

        xs = np.arange(w, dtype=np.float32)
        ys = np.arange(h, dtype=np.float32)
        map_x, map_y = np.meshgrid(xs, ys)

        dx = map_x - cx
        dy = map_y - cy
        r = np.sqrt(dx * dx + dy * dy).astype(np.float32)
        theta = np.arctan2(dy, dx).astype(np.float32)

        fall = self._compute_falloff(r, R).astype(np.float32)
        swirl_amount = self.strength * fall

        self.band_period = self.radius / 2.0 
        if not self.band_period or self.band_period > 0:
            band = np.sin((2.0 * np.pi * r) / float(self.band_period)).astype(np.float32)
            swirl_amount = swirl_amount * band

        theta_new = theta + swirl_amount

        map_x_new = (cx + r * np.cos(theta_new)).astype(np.float32)
        map_y_new = (cy + r * np.sin(theta_new)).astype(np.float32)

        warped = cv2.remap(
            img_np,
            map_x_new,
            map_y_new,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT_101
        )

        return warped
