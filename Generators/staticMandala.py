# Generators/staticMandala.py
from .staticGenerator import StaticGenerator

class StaticMandala(StaticGenerator):
    """Copies pre-saved mandala images into the mandala output directory."""

    def __init__(self):
        super().__init__()

    @property
    def input_dir(self) -> str:
        return self.config["paths"]["static_mandalas"]

    @property
    def output_dir(self) -> str:
        return self.config["paths"]["mandalas_out"]

    @property
    def file_count_key(self) -> str:
        return "static_mandalas"

    @property
    def base_filename(self) -> str:
        return "static_mandala"
