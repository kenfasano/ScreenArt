import numpy as np #type: ignore
from ..base import Transformer

class RasterTransformer(Transformer):
    """
    The concrete base class for all image/raster based transformers.
    """
    def __init__(self):
        # Initialize the storage for metadata
        self.metadata_dictionary = {}

    def get_image_metadata(self) -> str:
        """
        Generically converts self.metadata_dictionary into a string.
        Format: "Key:Value;Key:Value"
        If empty, returns the Class Name.
        """
        if not self.metadata_dictionary:
            return ""
        
        # Sort keys to ensure consistent filename strings regardless of insertion order
        parts = []
        for k, v in sorted(self.metadata_dictionary.items()):
            # specialized formatting for lists/tuples to keep them short
            if isinstance(v, (list, tuple)):
                val_str = f"{','.join(v)}"
            elif isinstance(v, float):
                val_str = f"{v:.2f}"
            else:
                val_str = str(v)
            
            parts.append(f"{k}={val_str}")
            
        return ",".join(parts)

    def apply(self, config: dict, img_np: np.ndarray) -> np.ndarray:
        # Default pass-through, override in subclasses
        return img_np
