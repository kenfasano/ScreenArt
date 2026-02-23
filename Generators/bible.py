import json
import os
import random
from .text import Text

class Bible(Text):
    def __init__(self):
        super().__init__()
        
        bible_config = self.config.get("bible", {})
        self.file_count = bible_config.get("file_count", 3)
        
        self.books = [
            ["HebrewPsalms", 150],
            ["UkrainianPsalms", 150]
        ]
        
        self.colors = [
            ("white", "black"), ("yellow", "blue"),
            ("orange", "purple"), ("red", "white"),
            ("green", "white"), ("blue", "white"),
            ("purple", "white"), ("black", "white")
        ]

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
            self.log.error(f"'{book_item}' cannot be split into language and book.")
            return (book_item, "English") 

    def format_text(self, text_list: list[dict[str, str]]) -> list[str]:
        text_lines: list[str] = []
        for verse_obj in text_list:
            if verse_obj.get('number'):
                formatted_line = f"{verse_obj['number']}. {verse_obj['text']}" 
            else:
                formatted_line = f"{verse_obj['text']}" 
            text_lines.append(formatted_line)
        return text_lines

    def run(self, *args, **kwargs):
        self.log.info(f"Running Bible Generator (Target: {self.file_count} images)...")
        
        out_dir = os.path.join(self.config["paths"]["generators_in"], "bible")
        os.makedirs(out_dir, exist_ok=True)
        
        # FIXED: Points directly to Generators/Data
        input_base_dir = os.path.join(self.base_path, "Generators", "Data")
        self.log.info(f"{input_base_dir=}")

        for _ in range(self.file_count):
            book = random.choice(self.books)
            language_book = book[0]
            chapter = random.randint(1, book[1])
            
            book_name, language = self.get_name_and_language(language_book)
            base_filename = f"{book_name.lower()}_{chapter}"
            
            # Joins to Generators/Data/HebrewPsalms/hebrewpsalms_1.json
            input_file_path = os.path.join(input_base_dir, language_book, f"{base_filename}.json")
            
            if not os.path.exists(input_file_path):
                self.log.warning(f"Input file not found, skipping: {input_file_path}")
                continue

            try:
                with open(input_file_path, 'r', encoding='utf-8') as f:
                    dictionary_list = json.load(f)
                    lines_to_draw = self.format_text(dictionary_list)
            except Exception as e:
                self.log.error(f"Failed to load or parse JSON {input_file_path}: {e}")
                continue
                
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
            
            output_file_path = os.path.join(out_dir, f"{base_filename}.png")
            try:
                img.save(output_file_path)
                self.log.debug(f"Saved Bible image: {output_file_path}")
            except Exception as e:
                self.log.error(f"Failed to save image {output_file_path}: {e}")

        self.log.info("Bible Generator finished.")
