import numpy as np
import cv2
import random
from scipy.spatial import KDTree
from .rasterTransformer import RasterTransformer


class VoronoiTransformer(RasterTransformer):
    """
    Tessellates the image into Voronoi cells, each filled with the average
    colour of its source pixels. Produces a stained-glass / low-poly mosaic.
    Works at a downscaled canvas for speed, upscales with nearest-neighbour.
    """

    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("voronoitransformer", {})

        num_points = t_config.get("num_points")
        if not isinstance(num_points, int):
            num_points = random.randint(60, 350)

        edge_blend = t_config.get("edge_blend", True)
        if isinstance(edge_blend, str):
            edge_blend = True

        self.metadata_dictionary["num_points"] = num_points
        self.metadata_dictionary["edge_blend"] = int(edge_blend)

        img = self.to_uint8(img_np)
        h, w = img.shape[:2]

        scale = 0.35
        sh, sw = max(1, int(h * scale)), max(1, int(w * scale))
        small = cv2.resize(img, (sw, sh))

        pts = np.column_stack([
            np.random.uniform(0, sw, num_points),
            np.random.uniform(0, sh, num_points),
        ]).astype(np.float32)

        yy, xx = np.mgrid[0:sh, 0:sw]
        pixel_coords = np.stack([xx.ravel(), yy.ravel()], axis=1).astype(np.float32)
        _, nearest = KDTree(pts).query(pixel_coords, workers=-1)
        nearest = nearest.reshape(sh, sw)

        out_small = np.empty_like(small)
        for i in range(num_points):
            mask = nearest == i
            if mask.any():
                out_small[mask] = small[mask].mean(axis=0).astype(np.uint8)

        if edge_blend:
            edge_map = cv2.Laplacian(nearest.astype(np.float32), cv2.CV_32F)
            edge_mask = (np.abs(edge_map) > 0).astype(np.uint8)
            edge_mask_3 = cv2.cvtColor(edge_mask * 160, cv2.COLOR_GRAY2BGR)
            out_small = cv2.subtract(out_small, edge_mask_3)

        out = cv2.resize(out_small, (w, h), interpolation=cv2.INTER_NEAREST)
        return self.to_float32(out)
