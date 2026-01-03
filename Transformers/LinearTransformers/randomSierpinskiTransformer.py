import numpy as np # type: ignore
import random
from typing import Union, cast
from ..base import Transformer

class RandomSierpinskiTransformer(Transformer):
    """
    Generates a Sierpinski Triangle using the 'Chaos Game' algorithm.
    Instead of subdividing geometry, it generates a cloud of points
    by iteratively moving halfway towards random vertices.
    """
    def __init__(self, num_points: int = 50000):
        self.num_points = num_points

    def get_image_metadata(self) -> str:
        return f"Sierpinski_Chaos_{self.num_points}"

    def apply(self, config: dict, data: Union[int, float, np.ndarray]) -> Union[int, float, np.ndarray]:
        """
        Ignores input data structure (mostly) and returns a new point cloud
        constrained within the bounds of the input shape.
        """
        # 1. Type Guard
        if not isinstance(data, np.ndarray) or data.shape[0] < 3:
            return data
        
        points = cast(np.ndarray, data)
        
        # 2. Identify the 3 vertices (Corners)
        # We assume the input 'points' define the outer triangle.
        # If there are more than 3, we just take the first 3 or bounding box corners.
        # Ideally, input is just the 3 vertices of the triangle.
        vertices = points[:3]
        
        # 3. Initialize arrays for the Chaos Game
        # We perform this vectorized for speed, but the logic is iterative.
        # Since each point depends on the previous, simple vectorization is hard.
        # However, Numba would be fastest. For standard Numpy, we can try a loop 
        # or a pre-calculated index array approach if N is small.
        # Given 50k points, a python loop might be slow-ish but acceptable (~0.1s).
        
        new_points = np.zeros((self.num_points, 2))
        
        # Start at a random point inside the triangle (or just use a vertex)
        current_pos = vertices[0]
        
        # Pre-generate random vertex choices (0, 1, or 2)
        choices = np.random.randint(0, 3, size=self.num_points)
        
        # 4. Run the Chaos Game
        # (Optimized loop)
        for i in range(self.num_points):
            target = vertices[choices[i]]
            # Move halfway to target
            current_pos = (current_pos + target) * 0.5
            new_points[i] = current_pos
            
        return new_points
