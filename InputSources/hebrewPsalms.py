import json
import random
from . import text
from .. import log

class HebrewPsalms(text.Text):
    def __init__(self, config: dict | None = None):
        super().__init__(config.get("hebrewPsalms", None) if config else {})
        self.base_path = "HebrewPsalms"
        self.base_filename = "hebrewPsalms"
        log.info(f"HebrewPsalms {self.file_count=}")

    def format_text(self, text_list: list[dict[str, str]]) -> list[str]:
        text_lines: list[str] = []
        for verse_obj in text_list:
            if verse_obj['number']:
                formatted_line = f"{verse_obj['number']}. {verse_obj['text']}" 
            else:
                formatted_line = f"{verse_obj['text']}" 
            text_lines.append(formatted_line)

        return text_lines

    def load_list(self):
        psalm: int = random.randint(1,150)
        log.info(f"{psalm=}")

        file_path = f"ScreenArt/InputSources/Data/HebrewPsalms/psalm_{psalm}.json"
        self.language = "Hebrew"

        try:
            # Open and read the JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                dictionary_list= json.load(f)
                self.current_list = self.format_text(dictionary_list)

            log.info(f"Successfully loaded psalm in {self.language} from {file_path}.")
            log.info(f"{self.current_list=}")

        except FileNotFoundError:
            log.error(f"Error: The file '{file_path}' was not found.")
            self.current_list = [] # Initialize as empty list on failure
        except json.JSONDecodeError as e:
            log.error(f"Error: The file '{file_path}' contains invalid JSON: {e}")
            self.current_list = [] # Initialize as empty list on failure
        except SystemError as e:
            log.error(f"Error in hebrewPsalms.py: {e}")
            self.current_list = [] # Initialize as empty list on failure
