import numpy as np # type: ignore
import random

class SineWaveTransformer:
    def __init__(self, amplitude=10.0, frequency=0.05, axis='y'):
        self.amplitude = amplitude
        self.frequency = frequency
        self.axis = axis # 'x', 'y', or 'both'

    def apply(self, config: dict, points: np.ndarray) -> np.ndarray:
        # Randomize parameters if called without specific config
        amp = config.get("sine_amplitude", random.uniform(5.0, 30.0))
        freq = config.get("sine_frequency", random.uniform(0.01, 0.1))
        
        # Copy to avoid mutating original
        new_points = points.copy()
        
        x = new_points[:, 0]
        y = new_points[:, 1]
        
        # If we want to ripple Y, we use X as the input for Sin
        if self.axis == 'y' or self.axis == 'both':
            new_points[:, 1] += np.sin(x * freq) * amp
            
        # If we want to ripple X, we use Y as the input for Sin
        if self.axis == 'x' or self.axis == 'both':
            new_points[:, 0] += np.sin(y * freq) * amp
            
        return new_points
