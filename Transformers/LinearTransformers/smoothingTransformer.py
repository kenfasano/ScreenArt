import numpy as np
from .linearTransformer import LinearTransformer

class SmoothingTransformer(LinearTransformer):
    """
    Smoothes a point cloud using the Chaikin curve algorithm.
    """
    def __init__(self, iterations: int = 2, tension: float = 0.25):
        super().__init__()
        self.iterations = iterations
        self.tension = tension
        
        # Tag for filename tracking
        self.metadata_dictionary["smooth_iters"] = self.iterations
        self.metadata_dictionary["smooth_tens"] = round(self.tension, 2)

    def run(self, pts_array: np.ndarray, *args, **kwargs) -> np.ndarray:
        current_points = pts_array
        
        for _ in range(self.iterations):
            if len(current_points) < 2:
                break
                
            # p0 is the start of segment, p1 is the end.
            p0 = current_points[:-1]
            p1 = current_points[1:]
            
            # Calculate new points Q and R between p0 and p1
            Q = (1 - self.tension) * p0 + self.tension * p1
            R = self.tension * p0 + (1 - self.tension) * p1
            
            # Interleave Q and R
            new_points = np.empty((Q.shape[0] * 2, 2))
            new_points[0::2] = Q
            new_points[1::2] = R
            
            # Reattach the start and end points
            current_points = np.vstack([current_points[0], new_points, current_points[-1]])
            
        return current_points
