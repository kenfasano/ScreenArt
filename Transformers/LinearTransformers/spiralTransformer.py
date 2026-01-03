import numpy as np # type: ignore
from typing import Union, cast
from ..base import Transformer

class SpiralTransformer(Transformer):
    """
    Wraps 2D points into a logarithmic spiral or twists them based on distance.
    """
    def __init__(self, tightness: float = 0.5):
        self.tightness = tightness

    def get_image_metadata(self) -> str:
        return f"Spiral_t{self.tightness}"

    def apply(self, config: dict, data: Union[int, float, np.ndarray]) -> Union[int, float, np.ndarray]:
        # 1. Type Guard
        if not isinstance(data, np.ndarray):
            return data
        
        points = cast(np.ndarray, data)
        if points.shape[0] < 1:
            return points
        
        # 2. Calculate center of the shape to twist around it
        center = np.mean(points, axis=0)
        centered = points - center
        
        # 3. Convert to Polar Coordinates
        x = centered[:, 0]
        y = centered[:, 1]
        radii = np.sqrt(x**2 + y**2)
        angles = np.arctan2(y, x)
        
        # 4. Apply Spiral Twist
        # The angle twist increases with distance (radius)
        # Factor 0.01 scales it so 1.0 tightness isn't too extreme
        new_angles = angles + (radii * self.tightness * 0.01)
        
        # 5. Convert back to Cartesian
        new_x = radii * np.cos(new_angles)
        new_y = radii * np.sin(new_angles)
        
        # 6. Restore position
        result = np.column_stack((new_x, new_y)) + center
        return result
