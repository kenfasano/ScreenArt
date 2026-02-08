import numpy as np # type: ignore
from typing import Union, cast
from ..base import Transformer

class SierpinskiTransformer(Transformer):
    """
    Applies one iteration of Sierpinski Triangle subdivision logic.
    Shrinks the shape towards its center and creates 3 copies shifted 
    to the top, bottom-left, and bottom-right.
    """
    def __init__(self):
        pass

    def get_image_metadata(self) -> str:
        return "Sierpinski_Iter"

    def apply(self, config: dict, data: Union[int, float, np.ndarray]) -> Union[int, float, np.ndarray]:
        # 1. Type Guard
        if not isinstance(data, np.ndarray):
            return data
        points = cast(np.ndarray, data)
        if points.shape[0] < 1:
            return points
        
        # 2. Calculate Centroid
        centroid = np.mean(points, axis=0)
        
        # 3. Shrink the shape by half
        # (IFS Scale factor is usually 0.5 for Sierpinski)
        scaled_points = (points - centroid) * 0.5
        
        # 4. Calculate Bounds to determine shift distances
        min_x, min_y = np.min(points, axis=0)
        max_x, max_y = np.max(points, axis=0)
        w = max_x - min_x
        h = max_y - min_y
        
        # 5. Define Offsets 
        # For an upright triangle:
        # - Top copy moves UP (negative Y)
        # - Bottom copies move DOWN (positive Y) and OUT (left/right)
        shift_top = np.array([0, -h/4]) 
        shift_left = np.array([-w/4, h/4]) 
        shift_right = np.array([w/4, h/4]) 
        
        # 6. Create 3 copies
        shape1 = scaled_points + centroid + shift_top
        shape2 = scaled_points + centroid + shift_left
        shape3 = scaled_points + centroid + shift_right
        
        # 7. Stack them
        return np.vstack((shape1, shape2, shape3))
