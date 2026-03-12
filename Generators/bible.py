import json
import os
import random
from .text import Text

def _parse_language_book(lang_book: str) -> tuple[str, str]:
    """Split 'UkrainianPsalms' → ('Psalms', 'Ukrainian') at the second uppercase letter."""
    for i in range(1, len(lang_book)):
        if lang_book[i].isupper():
            return lang_book[i:], lang_book[:i]
    return lang_book, "English"


class Bible(Text):
    BOOKS = [
        ("HebrewPsalms", 150),
        ("UkrainianPsalms", 150),
    ]

    def __init__(self):
        super().__init__()
        self.input_base_dir = os.path.join(self.base_path, "Generators", "Data")
        self.out_dir = os.path.join(self.config["paths"]["generators_in"], "bible")
        os.makedirs(self.out_dir, exist_ok=True)

        self.file_count = self.config.get("bible", {}).get("file_count", 3)
        self.log.debug(f"Bible: {self.file_count=}")

        # Precompute (book_name, language) — avoids per-call string scanning
        self._book_meta = {
            lang_book: _parse_language_book(lang_book)
            for lang_book, _ in self.BOOKS
        }

    @staticmethod
    def _format_text(verse_list: list[dict]) -> list[str]:
        """Convert verse dicts to display strings."""
        return [
            f"{v['number']}. {v['text']}" if v.get('number') else v['text']
            for v in verse_list
        ]

    def _load_psalm(self, lang_book: str, chapter: int) -> list[str] | None:
        """Load and format a psalm file. Returns None on any failure."""
        book_name, _ = self._book_meta[lang_book]
        path = os.path.join(
            self.input_base_dir, lang_book,
            f"{book_name.lower()}_{chapter}.json"
        )
        try:
            with open(path, encoding='utf-8') as f:
                return self._format_text(json.load(f))
        except FileNotFoundError:
            self.log.debug(f"Psalm file not found: {path}")
        except Exception as e:
            self.log.debug(f"Failed to load {path}: {e}")
        return None

    def warm_cache(self) -> None:
        """Pre-compute and persist font sizes for all psalms in all books.
        Call once manually after adding or changing psalm data.
        """
        self.log.debug("Warming font size cache...")
        count = 0
        for lang_book, chapter_count in self.BOOKS:
            for chapter in range(1, chapter_count + 1):
                lines = self._load_psalm(lang_book, chapter)
                if lines:
                    _, language = self._book_meta[lang_book]
                    font_path = self.language_fonts.get(language, self.language_fonts["English"])
                    self._find_max_font_size(font_path, lines)
                    count += 1
        self.log.debug(f"Cache warmed with {count} entries.")

    def run(self, *args, **kwargs) -> None:
        for _ in range(self.file_count):
            lang_book, chapter_count = random.choice(self.BOOKS)
            chapter = random.randint(1, chapter_count)

            lines = self._load_psalm(lang_book, chapter)

            if not lines:
                self.log.debug(f"No lines for {lang_book} ch.{chapter}, skipping.")
                continue

            book_name, language = self._book_meta[lang_book]

            img, layout_mode = self.generate_text_image(
                lines_to_draw=lines,
                language=language,
            )

            out_path = os.path.join(self.out_dir, f"{book_name.lower()}_{chapter}.jpeg")
            try:
                img.convert("RGB").save(out_path, quality=95)
                meta_path = os.path.join(self.out_dir, f"{book_name.lower()}_{chapter}.json")
                with open(meta_path, "w", encoding="utf-8") as mf:
                    json.dump({"layout_mode": layout_mode}, mf)
                self.log.debug(f"Saved: {out_path} layout_mode={layout_mode}")
            except Exception as e:
                self.log.debug(f"Failed to save {out_path}: {e}")
