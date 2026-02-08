from typing import Protocol, runtime_checkable, Any, Dict
import numpy as np # type: ignore

@runtime_checkable
class Transformer(Protocol):
    """
    The base interface that all Transformers must adhere to.
    """
    def apply(self, config: Dict[str, Any], data: np.ndarray) -> np.ndarray:
        ...

    def get_image_metadata(self) -> str:
        """
        Returns a string representation of the transformer's settings.
        Implemented generically in the base class via self.metadata_dictionary.
        """
        ...
