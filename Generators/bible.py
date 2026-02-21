import json
import os
import random
from pathlib import Path
from .text import Text

class Bible(Text):
    def __init__(self):
        # 1. Initialize the parent (which sets up config, logs, and fonts)
        super().__init__()
        
        # 2. Grab config safely
        bible_config = self.config.get("bible", {})
        self.file_count = bible_config.get("file_count", 3)
        
        self.books = [
            ["HebrewPsalms", 150],
            ["UkrainianPsalms", 150]
        ]
        
        # Moved from the old Text.draw()
        self.colors = [
            ("white", "black"),
            ("yellow", "blue"),
            ("orange", "purple"),
            ("red", "white"),
            ("green", "white"),
            ("blue", "white"),
            ("purple", "white"),
            ("black", "white")
        ]

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
            self.log.error(f"'{book_item}' cannot be split into language and book.")
            return (book_item, "English") # Fallback instead of exiting

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
        """Replaces the old draw/load_list logic. Handles its own looping."""
        self.log.info(f"Running Bible Generator (Target: {self.file_count} images)...")
        
        # 1. Setup paths natively using inherited properties
        out_dir = os.path.join(self.config["paths"]["generators_in"], "bible")
        os.makedirs(out_dir, exist_ok=True)
        
        input_base_dir = os.path.join(self.base_path, "InputSources", "Bible")

        # 2. Main generation loop
        for _ in range(self.file_count):
            book = random.choice(self.books)
            language_book = book[0]
            chapter = random.randint(1, book[1])
            
            book_name, language = self.get_name_and_language(language_book)
            base_filename = f"{book_name.lower()}_{chapter}"
            
            input_file_path = os.path.join(input_base_dir, language_book, f"{base_filename}.json")
            
            # Load the JSON
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

            # Pick random colors
            bg_color, fg_color = random.choice(self.colors)
            
            # 3. Use the Text class to generate the canvas
            img = self.generate_text_image(
                lines_to_draw=lines_to_draw,
                language=language,
                bg_color=bg_color,
                fg_color=fg_color
            )
            
            # 4. Save the image natively using PIL
            output_file_path = os.path.join(out_dir, f"{base_filename}.png")
            try:
                img.save(output_file_path)
                self.log.debug(f"Saved Bible image: {output_file_path}")
            except Exception as e:
                self.log.error(f"Failed to save image {output_file_path}: {e}")

        self.log.info("Bible Generator finished.")
