# Generators/staticFavorites.py
from .staticGenerator import StaticGenerator

class StaticFavorites(StaticGenerator):
    """Copies pre-saved favorite images into the favorites output directory."""

    def __init__(self, out_dir: str):
        super().__init__(out_dir)

    @property
    def input_dir(self) -> str:
        return self.config["paths"]["static_favorites_in"]

    @property
    def output_dir(self) -> str:
        return self.out_dir

    @property
    def file_count_key(self) -> str:
        return "static_favorites"

    @property
    def base_filename(self) -> str:
        return "static_favorite"
