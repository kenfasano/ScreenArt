from abc import abstractmethod
import json
from typing import TextIO
import os

class ParseBible:
    def __init__(self, target_path: str, psalm_name: str, encoding="UTF-8"):
        self.psalm_name = psalm_name
        self.encoding = encoding
        expanded_path = os.path.expanduser(target_path)

        try:
            os.chdir(expanded_path)
            print(f"Successfully changed directory to: {os.getcwd()}")
        except FileNotFoundError:
            print(f"Error: The directory '{expanded_path}' was not found.")
            exit(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            exit(1)

    @abstractmethod
    def parse(self, content: str, chapter: int) -> list[str]:
        ...

    def write_line(self, f: TextIO, line: str):
        print(line)
        f.write(f"{line}\n")

    def write(self, results: list[str], book: str, chapter: int):
        # 1. Construct the data structure (List of Objects)
        data_structure = []
        data_structure.append({"number": "", "text": f"{chapter}. {self.psalm_name}"})
        for i, verse_text in enumerate(results):
            data_structure.append({
                "number": i + 1,
                "text": verse_text
            })

        # 2. Write the structure to the file
        # 'indent=4' makes it nicely formatted and readable.
        with open(f"{book}_{chapter}.json", "w") as f:
            json.dump(data_structure, f, indent=4, ensure_ascii=False)

    def run(self, book: str, num_chapters: int):
        for chapter in range(1, num_chapters + 1):
            try:
                with open(f"{book}_{chapter}.html", "r", encoding=self.encoding) as f:
                    contents = f.read()
                    results = self.parse(contents, chapter)
                    self.write(results, book, chapter)
            except FileNotFoundError:
                print(f"Error: '{book}_{chapter}.html' not found.")
