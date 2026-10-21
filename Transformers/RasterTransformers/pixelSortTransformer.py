import numpy as np
import random
from .rasterTransformer import RasterTransformer


class PixelSortTransformer(RasterTransformer):
    """
    Sorts pixels along rows or columns by a chosen key (brightness, hue, saturation).
    Only pixels within a threshold band are sorted, preserving structure in the rest.
    Creates flowing, glitchy streaks that follow the image's tonal contours.
    """

    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("pixelsorttransformer", {})

        # Direction: rows (horizontal streaks) or cols (vertical streaks)
        direction = t_config.get("direction")
        if not isinstance(direction, str) or direction not in ("rows", "cols"):
            direction = random.choice(("rows", "cols"))

        # Sort key: brightness, saturation, or red/green/blue channel
        sort_key = t_config.get("sort_key")
        if not isinstance(sort_key, str) or sort_key not in ("brightness", "saturation", "red", "green", "blue"):
            sort_key = random.choice(("brightness", "brightness", "saturation", "red", "green", "blue"))

        # Threshold: only pixels with key value in [low, high] are sorted
        low  = t_config.get("threshold_low")
        high = t_config.get("threshold_high")
        if not isinstance(low, (int, float)):
            low = random.uniform(0.05, 0.35)
        if not isinstance(high, (int, float)):
            high = random.uniform(0.55, 0.95)
        low, high = float(min(low, high)), float(max(low, high))

        self.metadata_dictionary["direction"] = direction
        self.metadata_dictionary["sort_key"]  = sort_key
        self.metadata_dictionary["low"]       = round(low, 2)
        self.metadata_dictionary["high"]      = round(high, 2)

        img = img_np.copy()  # float32 [0,1], BGR channel order from pipeline

        # Build sort-key map (float32 [0,1], same H×W)
        if sort_key == "brightness":
            key_map = img[..., 0] * 0.114 + img[..., 1] * 0.587 + img[..., 2] * 0.299
        elif sort_key == "saturation":
            cmax = img.max(axis=2)
            cmin = img.min(axis=2)
            key_map = np.where(cmax > 0, (cmax - cmin) / (cmax + 1e-6), 0.0)
        elif sort_key == "red":
            key_map = img[..., 2]   # BGR: index 2 = R
        elif sort_key == "green":
            key_map = img[..., 1]
        else:  # blue
            key_map = img[..., 0]

        mask = (key_map >= low) & (key_map <= high)

        if direction == "rows":
            for y in range(img.shape[0]):
                indices = np.where(mask[y])[0]
                if len(indices) < 2:
                    continue
                for run in _contiguous_runs(indices):
                    order = np.argsort(key_map[y, run])
                    img[y, run] = img[y, run[order]]
        else:
            for x in range(img.shape[1]):
                indices = np.where(mask[:, x])[0]
                if len(indices) < 2:
                    continue
                for run in _contiguous_runs(indices):
                    order = np.argsort(key_map[run, x])
                    img[run, x] = img[run, x][order]

        return img


def _contiguous_runs(indices: np.ndarray) -> list[np.ndarray]:
    """Split sorted index array into contiguous runs using vectorized numpy."""
    if len(indices) < 2:
        return [indices] if len(indices) == 1 else []
    breaks = np.where(np.diff(indices) > 1)[0] + 1
    return np.split(indices, breaks)
