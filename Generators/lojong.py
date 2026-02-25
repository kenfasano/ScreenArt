import json
import os
import random
from .text import Text

class Lojong(Text):
    def __init__(self):
        super().__init__()
        
        lojong_config = self.config.get("lojong", {})
        self.file_count = lojong_config.get("file_count", 3)
        
        self.colors = [
            ("white", "black"), ("yellow", "blue"),
            ("orange", "purple"), ("red", "white"),
            ("green", "white"), ("blue", "white"),
            ("purple", "white"), ("black", "white")
        ]

    def format_text(self, lojong_data: list[dict[str, str]]) -> list[str]:
        full_text_lines = []
        point: int = random.randint(1, 7)
        
        filtered_slogans = [
            slogan for slogan in lojong_data
            if slogan.get('point') == point
        ]

        if not filtered_slogans:
            self.log.warning(f"No slogans found for point {point}, picking random sample.")
            filtered_slogans = random.sample(lojong_data, min(len(lojong_data), 3))

        for i, slogan_obj in enumerate(filtered_slogans):
            if slogan_obj.get("point") and int(slogan_obj.get("point", 0)) != point:
                continue

            slogan_text = slogan_obj.get("text", "")

            if i == 0: 
                category = slogan_obj.get("category", "General")
                full_text_lines.append(f"#{point} — {category} —")

            full_text_lines.append(slogan_text)

        return full_text_lines

    def _load_json_data(self, file_path: str):
        if not os.path.exists(file_path):
            self.log.error(f"Error: The file '{file_path}' was not found.")
            return None

        encodings_to_try = ['utf-8', 'utf-16', 'utf-16-le', 'utf-8-sig', 'iso-8859-1']
        
        for enc in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=enc, errors='replace') as f:
                    return json.load(f)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                self.log.debug(f"Failed to load {file_path} with {enc}: {e}")
            except Exception as e:
                self.log.error(f"Unexpected error loading {file_path} with {enc}: {e}")
                
        self.log.critical(f"CRITICAL: Could not load {file_path} with any of the attempted encodings.")
        return None

    def run(self, *args, **kwargs):
        self.log.info(f"Running Lojong Generator (Target: {self.file_count} images)...")

        out_dir = os.path.join(self.config["paths"]["generators_in"], "lojong")
        self.log.info(f"{out_dir=}")
        os.makedirs(out_dir, exist_ok=True)
        
        # FIXED: Points directly to Generators/Data/Lojong
        input_base_dir = os.path.join(self.base_path, "Generators", "Data", "Lojong")

        for i in range(self.file_count):
            if random.choice(["eng", "tib"]) == "eng":
                filename = "lojong_slogans_eng.json"
                language = "English"
            else:
                filename = "lojong_slogans_tib.json"
                language = "Tibetan"
                
            input_file_path = os.path.join(input_base_dir, filename)
            
            raw_data = self._load_json_data(input_file_path)
            if not raw_data:
                continue
                
            lines_to_draw = self.format_text(raw_data)
            if not lines_to_draw:
                self.log.warning(f"No text extracted from {input_file_path}, skipping.")
                continue

            bg_color, fg_color = random.choice(self.colors)
            
            img = self.generate_text_image(
                lines_to_draw=lines_to_draw,
                language=language,
                bg_color=bg_color,
                fg_color=fg_color
            )
            
            output_file_path = os.path.join(out_dir, f"lojong_{i}.png")
            try:
                img.save(output_file_path)
                self.log.debug(f"Saved Lojong image: {output_file_path}")
            except Exception as e:
                self.log.error(f"Failed to save image {output_file_path}: {e}")

        self.log.info("Lojong Generator finished.")
