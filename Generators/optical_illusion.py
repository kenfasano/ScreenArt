from .drawGenerator import DrawGenerator

class OpticalIllusion(DrawGenerator):
    """
    Intermediate base class for optical illusion generators.
    """
    def __init__(self, out_dir: str):
        super().__init__(out_dir)
