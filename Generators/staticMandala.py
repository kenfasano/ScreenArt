# Generators/staticMandala.py
from .staticGenerator import StaticGenerator

class StaticMandala(StaticGenerator):
    """Copies pre-saved mandala images into the mandala output directory."""
    def __init__(self, out_dir: str):
        super().__init__(out_dir)

    @property
    def input_dir(self) -> str:
        return self.config["paths"]["static_mandala_in"]

    @property
    def output_dir(self) -> str:
        return self.out_dir

    @property
    def file_count_key(self) -> str:
        return "static_mandalas"

    @property
    def base_filename(self) -> str:
        return "static_mandala"
