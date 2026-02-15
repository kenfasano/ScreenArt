import random
from . import drawGenerator
from typing import Any # Import Any for flexible dicts

# Import the specific implementations
from .kochSnowflake1 import KochSnowflake1
from .kochSnowflake2 import KochSnowflake2
from .kochSnowflake3 import KochSnowflake3
from .kochSnowflake4 import KochSnowflake4

class KochSnowflake(drawGenerator.DrawGenerator):
    """
    Master KochSnowflake class.
    Does not draw directly. Instead, it randomly delegates the work to 
    KochSnowflake 1, 2, 3, or 4 based on specific probability weights.
    """
    def __init__(self, config: dict[str, Any]):
        super().__init__(config, "kochsnowflake")

    def draw(self):
        # Define the available generator classes
        generators = [
            KochSnowflake1, 
            KochSnowflake2, 
            KochSnowflake3, 
            KochSnowflake4
        ]
        
        # Define the specific probability weights (3:4:5:6)
        # 1: 3/18 (~16.6%)
        # 2: 4/18 (~22.2%)
        # 3: 5/18 (~27.7%)
        # 4: 6/18 (~33.3%)
        weights = [3, 4, 5, 6]
        
        # Select one class based on the defined weights
        # random.choices returns a list, so we grab the first element
        SelectedGeneratorClass = random.choices(generators, weights=weights, k=1)[0]
        
        # Instantiate the selected generator with the original configuration
        generator_instance = SelectedGeneratorClass(self.config)
        
        # Delegate the draw call
        generator_instance.draw()
