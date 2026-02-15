from abc import abstractmethod
from . import base
from typing import Any # Import Any for flexible dicts

class DrawGenerator(base.Base):
    def __init__(self, config: dict[str, Any], sub_config_key: str):
        super().__init__(config, sub_config_key)

    @abstractmethod
    def draw(self, *args, **kwargs):
        pass
