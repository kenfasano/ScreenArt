import numpy as np
from .linearTransformer import LinearTransformer

class KochSnowflakeTransformer(LinearTransformer):
    """
    Applies a single iteration of the Koch Snowflake fractal generation
    to a set of 2D points (represented as a numpy array).
    """
    def __init__(self):
        super().__init__()
        # Tag for the filename metadata
        self.metadata_dictionary["type"] = "KochSnowflake"

    def run(self, pts_array: np.ndarray, *args, **kwargs) -> np.ndarray:
        """
        Applies one iteration of the Koch curve subdivision to the input points.
        Expects: (N, 2) numpy array of points.
        Returns: (~4N, 2) numpy array with the fractal details added.
        """
        if pts_array.shape[0] < 2:
            return pts_array

        # Pre-calculate rotation matrix for +60 degrees (pi/3)
        theta = np.pi / 3
        rotation_matrix = np.array([
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta),  np.cos(theta)]
        ])

        # Get start (p1) and end (p5) points of each existing segment
        p1 = pts_array[:-1]
        p5 = pts_array[1:]
        
        # Calculate the vector between points
        diff = p5 - p1
        
        # Calculate intermediate points along the segment
        p2 = p1 + diff / 3.0
        p4 = p1 + (diff * 2.0) / 3.0
        
        # Calculate p3 (Peak of the triangle)
        segment_third = diff / 3.0
        rotated_vec = segment_third @ rotation_matrix.T
        p3 = p2 + rotated_vec

        # Stack points in order: p1, p2, p3, p4
        new_segments = np.stack((p1, p2, p3, p4), axis=1)
        
        # Flatten to (Total_Points, 2) and append the final closing point
        new_points = new_segments.reshape(-1, 2)
        result = np.vstack((new_points, pts_array[-1]))
        
        return result
