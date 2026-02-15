from abc import ABC
from typing import Any # Import Any for flexible dicts

class Base(ABC):
    def __init__(self, config: dict[str, Any], sub_config_key: str):
        super().__init__()
        # Ensure config is at least an empty dict so .get() never fails
        safe_config = config or {}
        self.config = safe_config.get(sub_config_key, {})
        self.paths = safe_config.get("paths", {})

    def get_path(self, path_key: str) -> str:
        return self.paths.get(path_key, "")
