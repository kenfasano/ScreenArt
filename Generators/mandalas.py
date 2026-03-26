import random
from .drawGenerator import DrawGenerator
from .staticMandala import StaticMandala

class Mandalas(DrawGenerator):
    """
    Master Mandalas class.
    Randomly delegates the work to StaticMandala and others
    """

    def __init__(self):
        super().__init__()

    def run(self, *args, **kwargs) -> None:
        self.log.debug("Running Master Mandala Generator...")
        
        # generators = [KochSnowflake1, KochSnowflake2, KochSnowflake3, KochSnowflake4]
        generators = [StaticMandala]
        weights = [3]

        SelectedGeneratorClass = random.choices(generators, weights=weights, k=1)[0]
        
        # Instantiate without passing config, and call run()
        generator_instance = SelectedGeneratorClass()
        generator_instance.run()
