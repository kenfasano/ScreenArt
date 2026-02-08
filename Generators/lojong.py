import json
import os
import random
from pathlib import Path
from . import text
from .. import log
from .. import config  # Import config directly

DEFAULT_FILE_COUNT = 3

class Lojong(text.Text):
    def __init__(self, config_dict: dict):
        from .. import common
        self.config = common.get_config(config_dict, "lojong")
        self.file_count = self.config.get("file_count", DEFAULT_FILE_COUNT) if self.config else DEFAULT_FILE_COUNT

        # --- FIX: Use Path objects ---
        # Points to .../ScreenArt/InputSources/Data/Lojong
        lojong_directory = config.PROJECT_ROOT / "InputSources/Data/Lojong"
        output_base_path = Path(common.GENERATORS_IN) / "Lojong"
        
        # Ensure output exists
        output_base_path.mkdir(parents=True, exist_ok=True)

        input_file_paths: list[str] = []
        output_file_paths: list[str] = []
        languages: list[str] = []

        self.base_filename = "lojong"
        
        for i in range(self.file_count):
            if random.choice(["eng", "tib"]) == "eng":
                file_path = lojong_directory / "lojong_slogans_eng.json"
                languages.append("English")
            else:
                file_path = lojong_directory / "lojong_slogans_tib.json"
                languages.append("Tibetan")

            if not file_path.exists():
                log.warning(f"Lojong file missing: {file_path}")
                continue

            input_file_paths.append(str(file_path))
            output_file_paths.append(str(output_base_path / f"{self.base_filename}_{i}.jpeg"))

        super().__init__(input_file_paths, 
                         output_file_paths, 
                         self.config, 
                         languages)

    # ... (Keep the rest of your methods: format_text, load_list, etc.) ...
    def format_text(self, lojong_data):
        # (Paste your existing format_text method here)
        full_text_lines = []
        point = random.randint(1, 7)
        filtered_slogans = [s for s in lojong_data if s.get('point') == point]
        if not filtered_slogans:
            filtered_slogans = random.sample(lojong_data, min(len(lojong_data), 3))
        for i, slogan_obj in enumerate(filtered_slogans):
            if slogan_obj.get("point") and int(slogan_obj.get("point")) != point: continue
            slogan_text = slogan_obj.get("text", "")
            if i == 0: 
                category = slogan_obj.get("category", "General")
                full_text_lines.append(f"#{point} — {category} —")
            full_text_lines.append(slogan_text)
        return full_text_lines

    def load_list(self, i: int):
        if i >= len(self.input_file_paths): return
        file_path = self.input_file_paths[i]
        self.language = self.languages[i]
        try:
            # Try loading with utf-8 first
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                data = json.load(f)
            self.current_list = self.format_text(data)
        except Exception as e:
            log.error(f"Error loading Lojong {file_path}: {e}")
            self.current_list = []

