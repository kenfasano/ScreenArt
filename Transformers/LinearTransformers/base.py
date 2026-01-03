from typing import Union
import numpy as np # type: ignore
from ..base import Transformer

class LinearTransformer(Transformer):
    """
    Represents a linear transformation (y = mx + b).
    Unlike RasterTransformer, this holds parameters, not a grid.
    """
    def __init__(self, slope: float = 1.0, intercept: float = 0.0):
        self.slope = slope
        self.intercept = intercept

    def get_image_metadata(self) -> str:
        # Naming based on the math parameters
        return f"Linear_m{self.slope}_b{self.intercept}"

    def apply(self, config: dict, data: Union[int, float, np.ndarray]) -> Union[int, float, np.ndarray]:
        """Applies the linear calculation to the input data."""
        return (data * self.slope) + self.intercept
