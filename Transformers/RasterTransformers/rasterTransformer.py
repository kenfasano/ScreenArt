import numpy as np #type: ignore
from ..transformer import Transformer
class RasterTransformer(Transformer):
    """
    The concrete base class for all image/raster based transformers.
    """
    def __init__(self):
        # 1. Call super() to get self.config and self.log from ScreenArt
        super().__init__()
        self.metadata_dictionary = {}

    def get_image_metadata(self) -> str:
        """Generically converts self.metadata_dictionary into a string.
        Format: "Key:Value;Key:Value"
        If empty, returns the Class Name.
        """
        if not self.metadata_dictionary:
            self.log.warning(f"No metadata_dictionary for {self.__class__.__name__}")
            return ""
        
        # Sort keys to ensure consistent filename strings regardless of insertion order
        parts = []
        for k, v in sorted(self.metadata_dictionary.items()):
            # specialized formatting for lists/tuples to keep them short
            if isinstance(v, (list, tuple)):
                val_str = f"{','.join(str(v))}"
            elif isinstance(v, float):
                val_str = f"{v:.2f}"
            else:
                val_str = str(v)
            
            parts.append(f"{k}={val_str}")
            
        return ",".join(parts)

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        """
        Replaces apply(). Takes an image array and returns an image array.
        Default is pass-through; concrete children will override this.
        """
        return img_np
