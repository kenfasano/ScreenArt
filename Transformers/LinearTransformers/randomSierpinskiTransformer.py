import numpy as np
from numba import njit
from .linearTransformer import LinearTransformer


@njit(cache=True, fastmath=True)
def chaos_game(vertices, choices):
    num_points = len(choices)
    pts = np.empty((num_points, 2), dtype=np.float32)

    current = vertices[0].copy()

    for i in range(num_points):
        v = vertices[choices[i]]

        current[0] = (current[0] + v[0]) * 0.5
        current[1] = (current[1] + v[1]) * 0.5

        pts[i, 0] = current[0]
        pts[i, 1] = current[1]

    return pts


class RandomSierpinskiTransformer(LinearTransformer):

    def __init__(self, num_points: int = 50000):
        super().__init__()
        self.num_points = num_points
        self.metadata_dictionary["chaos_points"] = self.num_points

    def run(self, pts_array: np.ndarray, *args, **kwargs) -> np.ndarray:
        if pts_array.shape[0] < 3:
            return pts_array

        vertices = pts_array[:3].astype(np.float32)
        choices = np.random.randint(0, 3, size=self.num_points)

        return chaos_game(vertices, choices)
