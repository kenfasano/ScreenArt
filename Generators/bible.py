import json
import os
import random
from pathlib import Path
from . import text
from .. import log
from .. import config  # Import config directly

LANGUAGE_BOOK_INDEX = 0
CHAPTER_INDEX = 1
DEFAULT_FILE_COUNT = 3

books = [
        ["HebrewPsalms", 150],
        ["UkrainianPsalms", 150]
]

class Bible(text.Text):
    def __init__(self, config_dict: dict):
        # Import common only for getting the specific config dict
        from .. import common
        self.config = common.get_config(config_dict, "bible")
        self.file_count = self.config.get("file_count", DEFAULT_FILE_COUNT) if self.config else DEFAULT_FILE_COUNT

        input_file_paths: list[str] = []
        output_file_paths: list[str] = []
        self.languages: list[str] = []

        # --- FIX: Use Path objects from config.py ---
        # This prevents "Double Path" errors (InputSources/Data/InputSources...)
        # We start from PROJECT_ROOT and build down.
        bible_source_root = config.PROJECT_ROOT / "InputSources/Bible"
        output_root = Path(common.GENERATORS_IN) / "Bible"

        # Ensure output directory exists
        output_root.mkdir(parents=True, exist_ok=True)

        for _ in range(self.file_count):
            book = random.choice(books)
            language_book = book[LANGUAGE_BOOK_INDEX]
            chapter: int = random.randint(1, book[CHAPTER_INDEX])
            
            book_name, language = self.get_name_and_language(language_book)
            book_name = book_name.lower()
            base_filename = f"{book_name}_{chapter}"
            self.languages.append(language)

            # Construct Input Path safely
            input_path = bible_source_root / language_book / f"{base_filename}.json"
            
            if not input_path.exists():
                log.error(f"Missing Bible Source: {input_path}")
                continue

            input_file_paths.append(str(input_path))
            output_file_paths.append(str(output_root / f"{base_filename}.json"))

        super().__init__(input_file_paths, 
                         output_file_paths,
                         self.config, 
                         self.languages)

    def get_name_and_language(self, book_item: str) -> tuple[str, str]:
        split_index = -1
        for i in range(1, len(book_item)):
            if book_item[i].isupper():
                split_index = i
                break

        if split_index != -1:
            book_name = book_item[split_index:]
            language = book_item[:split_index] or "English"
            return (book_name, language)
        else:
            # Don't exit(1) on a data error, just log and return defaults
            log.error(f"Could not parse book name: {book_item}")
            return ("unknown", "English")

    def format_text(self, text_list: list[dict[str, str]]):
        text_lines: list[str] = []
        for verse_obj in text_list:
            if verse_obj.get('number'):
                formatted_line = f"{verse_obj['number']}. {verse_obj['text']}" 
            else:
                formatted_line = f"{verse_obj['text']}" 
            text_lines.append(formatted_line)
        return text_lines

    def load_list(self, i: int):
        if i >= len(self.input_file_paths):
            return

        try:
            with open(self.input_file_paths[i], 'r', encoding='utf-8') as f:
                dictionary_list = json.load(f)
                self.current_list = self.format_text(dictionary_list)
        except Exception as e:
            log.error(f"Error loading bible file {self.input_file_paths[i]}: {e}")
            self.current_list = []
