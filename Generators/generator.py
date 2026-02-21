# Generators/generator.py
from ScreenArt.screenArt import ScreenArt
from abc import abstractmethod

class Generator(ScreenArt):
    """
    The base class for all image generators. 
    Inherits config, paths, and logging from ScreenArt.
    """
    def __init__(self):
        # Initializes the ScreenArt superclass
        super().__init__()
        
        # If there are any shared setup steps that ALL generators 
        # (both text and image) need, they go here.

    @abstractmethod
    def run(self, *args, **kwargs):
        """Every Generator must implement its own run logic."""
        pass
