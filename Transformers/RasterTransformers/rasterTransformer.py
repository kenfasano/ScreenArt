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

    # In rasterTransformer.py — add these two helpers
    def to_uint8(self, img_np: np.ndarray) -> np.ndarray:
        """Convert float32 [0,1] pipeline format to uint8 for PIL/cv2 operations."""
        if img_np.dtype == np.float32 or img_np.dtype == np.float64:
            return np.clip(img_np * 255.0, 0, 255).astype(np.uint8)
        return img_np

    def to_float32(self, img_np: np.ndarray) -> np.ndarray:
        """Convert uint8 back to float32 [0,1] for pipeline return."""
        if img_np.dtype == np.uint8:
            return img_np.astype(np.float32) / 255.0
        return img_np

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        """
        Replaces apply(). Takes an image array and returns an image array.
        Default is pass-through; concrete children will override this.
        """
        return img_np
