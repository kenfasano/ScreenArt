import numpy as np # type: ignore

class SmoothingTransformer:
    def __init__(self, iterations=2, tension=0.25):
        """
        iterations: How many times to smooth. 1 = chamfered corners, 3 = smooth curve.
        tension: 0.25 is standard Chaikin (cuts corners at 25% and 75%).
        """
        self.iterations = iterations
        self.tension = tension

    def apply(self, config: dict, points: np.ndarray) -> np.ndarray:
        # If config is passed, allow overrides
        iters = config.get("smoothing_iterations", self.iterations)
        
        current_points = points
        
        for _ in range(iters):
            if len(current_points) < 2:
                break
                
            # We work with segments. 
            # p0 is the start of segment, p1 is the end.
            p0 = current_points[:-1]
            p1 = current_points[1:]
            
            # Calculate new points Q and R between p0 and p1
            # Q = 0.75*p0 + 0.25*p1
            # R = 0.25*p0 + 0.75*p1
            Q = (1 - self.tension) * p0 + self.tension * p1
            R = self.tension * p0 + (1 - self.tension) * p1
            
            # Interleave Q and R: Q0, R0, Q1, R1...
            # We stack them and then reshape to flatten
            new_points = np.empty((Q.shape[0] * 2, 2))
            new_points[0::2] = Q
            new_points[1::2] = R
            
            # Add the very first and very last original points to close the gap? 
            # Or just keep the floating segments. 
            # Typically Chaikin shrinks the line slightly, so we add start/end back.
            current_points = np.vstack([points[0], new_points, points[-1]])
            
        return current_points
