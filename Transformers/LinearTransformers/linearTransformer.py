from typing import Union
import numpy as np # type: ignore
from ..transformer import Transformer

class LinearTransformer(Transformer):
    """
    Represents a linear transformation (y = mx + b).
    Unlike RasterTransformer, this holds parameters, not a grid.
    """
    def __init__(self, slope: float = 1.0, intercept: float = 0.0):
        # 1. Inherit the ScreenArt ecosystem (config, log, paths)
        super().__init__()
        
        self.metadata_dictionary = {}
        self.slope = slope
        self.intercept = intercept

        # If this base class actually applies a slope/intercept, record it
        if self.slope != 1.0 or self.intercept != 0.0:
            self.metadata_dictionary["m"] = self.slope
            self.metadata_dictionary["b"] = self.intercept

    def get_image_metadata(self) -> str:
        # Naming based on the math parameters
        return f"Linear_m{self.slope}_b{self.intercept}"

    # 2. The New Standardized Contract
    def run(self, data: Union[int, float, np.ndarray], *args, **kwargs) -> Union[int, float, np.ndarray]:
        """
        Replaces apply(). Applies the linear calculation to the input data.
        The config parameter is removed, as self.config is natively available.
        """
        return (data * self.slope) + self.intercept
