import numpy as np
import random
from typing import Optional
from .linearTransformer import LinearTransformer

class SineWaveTransformer(LinearTransformer):
    """
    Applies a sine wave ripple across the X, Y, or both axes of a point cloud.
    """
    def __init__(self, amplitude: Optional[float] = None, frequency: Optional[float] = None, axis: str = 'y'):
        super().__init__()
        self.axis = axis
        
        # Default to random spreads if specific parameters aren't provided
        self.amplitude = amplitude if amplitude is not None else random.uniform(5.0, 30.0)
        self.frequency = frequency if frequency is not None else random.uniform(0.01, 0.1)
        
        self.metadata_dictionary["sine_amp"] = round(self.amplitude, 2)
        self.metadata_dictionary["sine_freq"] = round(self.frequency, 3)
        self.metadata_dictionary["sine_axis"] = self.axis

    def run(self, pts_array: np.ndarray, *args, **kwargs) -> np.ndarray:
        # Copy to avoid mutating original
        new_points = pts_array.copy()
        
        x = new_points[:, 0]
        y = new_points[:, 1]
        
        # Ripple Y
        if self.axis in ('y', 'both'):
            new_points[:, 1] += np.sin(x * self.frequency) * self.amplitude
            
        # Ripple X
        if self.axis in ('x', 'both'):
            new_points[:, 0] += np.sin(y * self.frequency) * self.amplitude
            
        return new_points
