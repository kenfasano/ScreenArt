import numpy as np # type: ignore
import random

class JitterTransformer:
    def __init__(self, intensity=2.0):
        self.intensity = intensity

    def apply(self, config: dict, points: np.ndarray) -> np.ndarray:
        intensity = config.get("jitter_intensity", random.uniform(1.0, 5.0))
        
        # Generate random noise for X and Y matching the shape of points
        noise = np.random.uniform(-intensity, intensity, points.shape)
        
        return points + noise
