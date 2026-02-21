import numpy as np
# Inherit from your new DRY LinearTransformer
from .linearTransformer import LinearTransformer

class SpiralTransformer(LinearTransformer):
    """
    Wraps 2D points into a logarithmic spiral or twists them based on distance.
    """
    def __init__(self, tightness: float = 0.5):
        super().__init__()
        self.tightness = tightness
        
        # Parent handles metadata string generation
        self.metadata_dictionary["spiral_t"] = round(self.tightness, 2)

    def run(self, pts_array: np.ndarray, *args, **kwargs) -> np.ndarray:
        # Shape Check
        if pts_array.shape[0] < 1:
            return pts_array
        
        # Calculate center of the shape to twist around it
        center = np.mean(pts_array, axis=0)
        centered = pts_array - center
        
        # Convert to Polar Coordinates
        x = centered[:, 0]
        y = centered[:, 1]
        radii = np.sqrt(x**2 + y**2)
        angles = np.arctan2(y, x)
        
        # Apply Spiral Twist
        new_angles = angles + (radii * self.tightness * 0.01)
        
        # Convert back to Cartesian
        new_x = radii * np.cos(new_angles)
        new_y = radii * np.sin(new_angles)
        
        # Restore position
        return np.column_stack((new_x, new_y)) + center
