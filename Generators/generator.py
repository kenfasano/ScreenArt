# Generators/generator.py
from ScreenArt.screenArt import ScreenArt
from abc import abstractmethod
import os
import shutil

class Generator(ScreenArt):
    """
    The base class for all image generators. 
    Inherits config, paths, and logging from ScreenArt.
    """
    def __init__(self, out_dir: str):
        # Initializes the ScreenArt superclass
        super().__init__()
        self.out_dir = out_dir
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)
        os.makedirs(self.out_dir)
        
        # If there are any shared setup steps that ALL generators 
        # (both text and image) need, they go here.

    @abstractmethod
    def run(self, *args, **kwargs):
        """Every Generator must implement its own run logic."""
        pass
