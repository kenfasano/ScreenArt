import json
from .. import log
import os
import random
from . import text
from typing import Any # Import Any for flexible dicts

DEFAULT_FILE_COUNT = 3

class Lojong(text.Text):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config, "lojong")
        self.file_count = self.config.get("file_count", DEFAULT_FILE_COUNT) if self.config else DEFAULT_FILE_COUNT

        lojong_directory = f"{self.paths["base_path"]}InputSources/Data/Lojong"
        
        # Initialize lists
        input_file_paths: list[str] = []
        output_file_paths: list[str] = []
        languages: list[str] = []

        self.base_filename = "lojong"
        
        for i in range(self.file_count):
            # Randomly choose language
            if random.choice(["eng", "tib"]) == "eng":
                input_file_paths.append(f"{lojong_directory}/lojong_slogans_eng.json")
                languages.append("English")
            else:
                input_file_paths.append(f"{lojong_directory}/lojong_slogans_tib.json")
                languages.append("Tibetan")

            output_base_path = f"{self.paths["generators_in"]}/Lojong"
            output_file_paths.append(f"{output_base_path}/{self.base_filename}_{i}.jpeg")

        super().init_fields(input_file_paths, 
                         output_file_paths, 
                         languages)

    def format_text(self, lojong_data: list[dict[str, str]]):
        full_text_lines = []
        point: int = random.randint(1, 7)
        
        filtered_slogans = [
            slogan for slogan in lojong_data
            if slogan.get('point') == point
        ]

        if not filtered_slogans:
            # Fallback: if point not found, just grab random ones
            log.warning(f"No slogans found for point {point}, picking random sample.")
            filtered_slogans = random.sample(lojong_data, min(len(lojong_data), 3))

        for i, slogan_obj in enumerate(filtered_slogans):
            # If we are in strict point mode, skip mismatches
            if slogan_obj.get("point") and int(slogan_obj.get("point", 0)) != point:
                continue

            slogan_text = slogan_obj.get("text", "")

            if i == 0: 
                category = slogan_obj.get("category", "General")
                full_text_lines.append(f"#{point} — {category} —")

            full_text_lines.append(slogan_text)

        return full_text_lines

    def load_list(self, i: int):
        file_path = self.input_file_paths[i]
        self.language = self.languages[i]
        self.current_list = []

        if not os.path.exists(file_path):
            log.error(f"Error: The file '{file_path}' was not found.")
            return

        # DEBUG: Read the first 4 bytes to see the actual file signature in the logs
        try:
            with open(file_path, 'rb') as f:
                _ = f.read(4)
        except Exception:
            pass

        # Encodings to try. Added utf-16-le specifically because of the 0xff start byte.
        encodings_to_try = ['utf-8', 'utf-16', 'utf-16-le', 'utf-8-sig', 'iso-8859-1']
        
        data = None
        loaded_successfully = False

        for enc in encodings_to_try:
            try:
                # CRITICAL FIX: errors='replace' prevents the "illegal surrogate" crash
                # It will replace corrupted characters with  instead of stopping execution.
                with open(file_path, 'r', encoding=enc, errors='replace') as f:
                    data = json.load(f)
                
                loaded_successfully = True
                break 
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                log.warning(f"Failed to load {file_path} with {enc}: {e}")
            except Exception as e:
                log.error(f"Unexpected error loading {file_path} with {enc}: {e}")

        if loaded_successfully and data:
            self.current_list = self.format_text(data)
        else:
            log.critical(f"CRITICAL: Could not load {file_path} with any of the attempted encodings.")
            self.current_list = []
