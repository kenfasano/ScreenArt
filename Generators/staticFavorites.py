# Generators/staticFavorites.py
from .staticGenerator import StaticGenerator

class StaticFavorites(StaticGenerator):
    """Copies pre-saved favorite images into the favorites output directory."""

    def __init__(self):
        super().__init__()

    @property
    def input_dir(self) -> str:
        return self.config["paths"]["static_favorites"]

    @property
    def output_dir(self) -> str:
        return self.config["paths"]["favorites_out"]

    @property
    def file_count_key(self) -> str:
        return "static_favorites"

    @property
    def base_filename(self) -> str:
        return "static_favorite"
