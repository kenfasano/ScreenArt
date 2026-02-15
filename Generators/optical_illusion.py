from . import drawGenerator
from typing import Any # Import Any for flexible dicts

class OpticalIllusion(drawGenerator.DrawGenerator):
    def __init__(self, config: dict[str, Any], sub_config_key: str):
        super().__init__(config, sub_config_key)
