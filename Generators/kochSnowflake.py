import random
from .drawGenerator import DrawGenerator

# Import the specific implementations
from .kochSnowflake1 import KochSnowflake1
from .kochSnowflake2 import KochSnowflake2
from .kochSnowflake3 import KochSnowflake3
from .kochSnowflake4 import KochSnowflake4

class KochSnowflake(DrawGenerator):
    """
    Master KochSnowflake class.
    Randomly delegates the work to KochSnowflake 1, 2, 3, or 4.
    """
    def __init__(self, out_dir: str):
        super().__init__(out_dir)

    def run(self, *args, **kwargs) -> None:
        self.log.debug("Running Master KochSnowflake Generator...")
        
        # generators = [KochSnowflake1, KochSnowflake2, KochSnowflake3, KochSnowflake4]
        generators = [KochSnowflake1, KochSnowflake2, KochSnowflake3, KochSnowflake4]
        weights = [1,1,1,1]
        SelectedGeneratorClass = random.choices(generators, weights=weights, k=1)[0]
        
        # Instantiate without passing config, and call run()
        generator_instance = SelectedGeneratorClass(self.out_dir)
        generator_instance.run()
