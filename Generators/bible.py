from .. import common
import json
import os
from pathlib import Path
import random
from . import text
from .. import log

LANGUAGE_BOOK_INDEX = 0
CHAPTER_INDEX = 1
DEFAULT_FILE_COUNT = 3

books = [
        ["HebrewPsalms", 150],
        ["UkrainianPsalms", 150]
]

class Bible(text.Text):
    def __init__(self, config: dict):
        import common
        self.config = common.get_config(config, "bible")
        self.file_count = self.config.get("file_count", DEFAULT_FILE_COUNT) if self.config else DEFAULT_FILE_COUNT

        input_file_paths: list[str] = []
        output_file_paths: list[str] = []
        self.languages: list[str] = []

        for _ in range(self.file_count):
            book = random.choice(books)
            language_book = book[LANGUAGE_BOOK_INDEX]
            chapter: int = random.randint(1, book[CHAPTER_INDEX])
            book_name, language = self.get_name_and_language(language_book)
            book_name = book_name.lower()
            base_filename: str = f"{book_name}_{chapter}"
            self.languages.append(language)

            input_base_path = f"{common.BASE_PATH}InputSources/Bible/{language_book}"
            if not os.path.exists(input_base_path):
                log.critical(f"No such directory: {input_base_path}")
                return
            input_file_paths.append(f"{input_base_path}/{base_filename}.json")

            output_base_path = f"{common.INPUT_SOURCES_IN}/Bible"
            if not os.path.exists(output_base_path):
                try:
                    new_directory = Path(output_base_path)
                    new_directory.mkdir(parents=True, exist_ok=True)
                    print(f"Directory created: {output_base_path}")
                except Exception as e:
                    print(f"An error occurred: {e}")

            output_file_paths.append(f"{output_base_path}/{base_filename}.json")

        # 3. Use the randomly selected books and chapters 
        super().__init__(input_file_paths, 
                         output_file_paths,
                         self.config, 
                         self.languages)

    def get_name_and_language(self, book_item: str) -> tuple[str, str]:
        split_index = -1
        # Iterate from the second character (index 1) to find the start of the second word
        for i in range(1, len(book_item)):
            if book_item[i].isupper():
                split_index = i
                break

        if split_index != -1:
            book_name = book_item[split_index:]
            language = book_item[:split_index] or "English"
            return (book_name, language)
        else:
            log.critical(f"{book_item} cannot be split into language and book.")
            exit(1)

    def format_text(self, text_list: list[dict[str, str]]):
        text_lines: list[str] = []
        for verse_obj in text_list:
            if verse_obj['number']:
                formatted_line = f"{verse_obj['number']}. {verse_obj['text']}" 
            else:
                formatted_line = f"{verse_obj['text']}" 
            text_lines.append(formatted_line)

        return text_lines

    def load_list(self, i: int):
        try:
            # Open and read the JSON file
            with open(self.input_file_paths[i], 'r', encoding='utf-8') as f:
                dictionary_list = json.load(f)
                self.current_list = self.format_text(dictionary_list)

        except FileNotFoundError:
            log.error(f"Error: The file '{self.input_file_paths[i]}' was not found.")
            self.current_list = [] # Initialize as empty list on failure
            self.language = self.languages[i]

        except json.JSONDecodeError as e:
            log.error(f"Error: The file '{self.input_file_paths[i]}' contains invalid JSON: {e}")
            self.current_list = [] # Initialize as empty list on failure

        except SystemError as e:
            log.error(f"Error in hebrewPsalms.py: {e}")
            self.current_list = [] # Initialize as empty list on failure
