from ScreenArt.screenArt import ScreenArt
from abc import abstractmethod

class Transformer(ScreenArt):
    """
    The base class for all image generators. 
    Inherits config, paths, and logging from ScreenArt.
    """
    def __init__(self):
        # Initializes the ScreenArt superclass
        super().__init__()
        
    @abstractmethod
    def run(self, *args, **kwargs):
        """Every Generator must implement its own run logic."""
        pass

    def get_image_metadata(self) -> str:
        """
        Returns a string representation of the transformer's settings.
        Implemented generically in the base class via self.metadata_dictionary.
        """
        ...
