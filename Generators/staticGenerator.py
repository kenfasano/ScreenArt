# Generators/staticGenerator.py
import os
import random
import shutil
from abc import abstractmethod
from .drawGenerator import DrawGenerator

class StaticGenerator(DrawGenerator):
    """
    Base class for generators that copy pre-saved images from a
    static source directory into an output directory.
    """
    def __init__(self, out_dir: str):
        super().__init__(out_dir)

    @property
    @abstractmethod
    def input_dir(self) -> str:
        """Absolute path to the source image directory."""
        ...

    @property
    @abstractmethod
    def output_dir(self) -> str:
        """Absolute path to the destination directory."""
        ...

    @property
    @abstractmethod
    def file_count_key(self) -> str:
        """Key used to look up file_counts in config."""
        ...

    @property
    @abstractmethod
    def base_filename(self) -> str:
        """Stem used when naming copied files (e.g. 'static_mandala')."""
        ...

    def run(self, *args, **kwargs) -> int:
        file_count = int(self.config.get("file_counts", {}).get(self.file_count_key, 1))
        files: list[str] = [
            f for f in os.listdir(self.input_dir)
            if f.lower().endswith((".jpeg", ".jpg", ".png"))
        ]

        if not files:
            return 0

        selected = random.sample(files, min(file_count, len(files)))

        for i, filename in enumerate(selected):
            self.log.info(f'staticGenerator <- {filename}')
            src = os.path.join(self.input_dir, filename)
            dst = os.path.join(self.output_dir, f"{self.base_filename}_{i}.jpeg")
            shutil.copy2(src, dst)

        return len(selected)
