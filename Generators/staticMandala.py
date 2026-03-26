import os
import random
import shutil
from .drawGenerator import DrawGenerator

class StaticMandala(DrawGenerator):
    """
    Generates static (pre-saved) mandala
    """
    def __init__(self):
        super().__init__()
        
    def run(self, *args, **kwargs):
        input_dir = self.config["paths"]["static_mandalas"]
        output_dir = self.config["paths"]["mandalas_out"]

        self.file_count = int(self.config.get("file_counts", {}).get("static_mandalas", 1))
        self.base_filename = "static_mandala"
        
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        files: list[str] = []
        for i in range(self.file_count):
            files = [
                f for f in os.listdir(input_dir)
                if f.lower().endswith((".jpeg", ".jpg", ".png"))
            ]  

        if not files:
            return 0

        selected = random.sample(files, min(self.file_count, len(files)))

        for i, filename in enumerate(selected):
            src = os.path.join(input_dir, filename)
            dst = os.path.join(output_dir, f"{self.base_filename}_{i}.jpeg")
            shutil.copy2(src, dst)

        return len(selected)
