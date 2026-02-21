import numpy as np
import random

# Inherit from your new DRY LinearTransformer
from .linearTransformer import LinearTransformer
from typing import Optional

class JitterTransformer(LinearTransformer):
    """
    Applies random uniform noise to a 2D point cloud.
    """
    def __init__(self, intensity: Optional[float] = None):
        super().__init__()
        
        # If no intensity is provided, default to a random spread (like your old config.get)
        self.intensity = intensity if intensity is not None else random.uniform(1.0, 5.0)
        
        # Tell the parent class about our settings for automatic filename tagging
        self.metadata_dictionary["jitter"] = round(self.intensity, 2)

    def run(self, pts_array: np.ndarray, *args, **kwargs) -> np.ndarray:
        """Applies jitter noise matching the shape of the point cloud."""
        
        noise = np.random.uniform(-self.intensity, self.intensity, pts_array.shape)
        return pts_array + noise
