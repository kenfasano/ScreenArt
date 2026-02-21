from typing import Union, cast
import numpy as np # type: ignore
from ..transformer import Transformer

class KochSnowflakeTransformer(Transformer):
    """
    Applies a single iteration of the Koch Snowflake fractal generation
    to a set of 2D points (represented as a numpy array).
    """
    def __init__(self):
        # No specific parameters needed for the standard 60-degree transform
        pass

    def get_image_metadata(self) -> str:
        return "KochSnowflake"

    def apply(self, config: dict, data: Union[int, float, np.ndarray]) -> Union[int, float, np.ndarray]:
        """
        Applies one iteration of the Koch curve subdivision to the input points.
        Expects: (N, 2) numpy array of points.
        Returns: (~4N, 2) numpy array with the fractal details added.
        """
        # 1. Type Guard: If it's not an array, return immediately.
        # This prevents AttributeError when accessing .shape on int/float.
        if not isinstance(data, np.ndarray):
            return data

        # 2. Explicit Cast: Tell the type checker that 'points' is definitely an ndarray.
        points = cast(np.ndarray, data)

        # 3. Shape Check: Safe to use .shape now
        if points.shape[0] < 2:
            return points

        # Pre-calculate rotation matrix for +60 degrees (pi/3)
        theta = np.pi / 3
        rotation_matrix = np.array([
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta),  np.cos(theta)]
        ])

        # 4. Get start (p1) and end (p5) points of each existing segment
        # 'points' is strictly typed as ndarray here, so slicing is valid.
        p1 = points[:-1]
        p5 = points[1:]
        
        # 5. Calculate the vector between points
        diff = p5 - p1
        
        # 6. Calculate intermediate points along the segment
        # p2 is at 1/3 mark, p4 is at 2/3 mark
        p2 = p1 + diff / 3.0
        p4 = p1 + (diff * 2.0) / 3.0
        
        # 7. Calculate p3 (Peak of the triangle)
        # Rotate the vector representing the middle third by 60 degrees
        segment_third = diff / 3.0
        rotated_vec = segment_third @ rotation_matrix.T
        p3 = p2 + rotated_vec

        # 8. Stack points in order: p1, p2, p3, p4
        new_segments = np.stack((p1, p2, p3, p4), axis=1)
        
        # 9. Flatten to (Total_Points, 2) and append the final closing point
        new_points = new_segments.reshape(-1, 2)
        result = np.vstack((new_points, points[-1]))
        
        return result
