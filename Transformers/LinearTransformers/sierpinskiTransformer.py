import numpy as np
# Inherit from your new DRY LinearTransformer
from .linearTransformer import LinearTransformer

class SierpinskiTransformer(LinearTransformer):
    """
    Applies one iteration of Sierpinski Triangle subdivision logic.
    Shrinks the shape towards its center and creates 3 copies shifted 
    to the top, bottom-left, and bottom-right.
    """
    def __init__(self):
        super().__init__()
        self.metadata_dictionary["type"] = "Sierpinski_Iter"

    def run(self, pts_array: np.ndarray, *args, **kwargs) -> np.ndarray:
        # 1. Shape Check
        if pts_array.shape[0] < 1:
            return pts_array
        
        # 2. Calculate Centroid
        centroid = np.mean(pts_array, axis=0)
        
        # 3. Shrink the shape by half
        # (IFS Scale factor is usually 0.5 for Sierpinski)
        scaled_points = (pts_array - centroid) * 0.5
        
        # 4. Calculate Bounds to determine shift distances
        min_x, min_y = np.min(pts_array, axis=0)
        max_x, max_y = np.max(pts_array, axis=0)
        w = max_x - min_x
        h = max_y - min_y
        
        # 5. Define Offsets 
        shift_top = np.array([0, -h/4]) 
        shift_left = np.array([-w/4, h/4]) 
        shift_right = np.array([w/4, h/4]) 
        
        # 6. Create 3 copies
        shape1 = scaled_points + centroid + shift_top
        shape2 = scaled_points + centroid + shift_left
        shape3 = scaled_points + centroid + shift_right
        
        # 7. Stack them
        return np.vstack((shape1, shape2, shape3))
