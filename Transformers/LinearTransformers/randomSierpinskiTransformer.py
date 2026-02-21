import numpy as np
# Inherit from your new DRY LinearTransformer
from .linearTransformer import LinearTransformer

class RandomSierpinskiTransformer(LinearTransformer):
    """
    Generates a Sierpinski Triangle using the 'Chaos Game' algorithm.
    Instead of subdividing geometry, it generates a cloud of points
    by iteratively moving halfway towards random vertices.
    """
    def __init__(self, num_points: int = 50000):
        super().__init__()
        self.num_points = num_points
        
        # The parent handles formatting this for the filename automatically
        self.metadata_dictionary["chaos_points"] = self.num_points

    def run(self, pts_array: np.ndarray, *args, **kwargs) -> np.ndarray:
        """
        Returns a new point cloud constrained within the bounds of the input shape.
        """
        # 1. Shape check (Type guard is no longer necessary)
        if pts_array.shape[0] < 3:
            return pts_array
        
        # 2. Identify the 3 vertices (Corners)
        vertices = pts_array[:3]
        
        # 3. Initialize arrays for the Chaos Game
        new_points = np.zeros((self.num_points, 2))
        
        # Start at a random point inside the triangle (or just use a vertex)
        current_pos = vertices[0]
        
        # Pre-generate random vertex choices (0, 1, or 2)
        choices = np.random.randint(0, 3, size=self.num_points)
        
        # 4. Run the Chaos Game
        for i in range(self.num_points):
            target = vertices[choices[i]]
            # Move halfway to target
            current_pos = (current_pos + target) * 0.5
            new_points[i] = current_pos
            
        return new_points
