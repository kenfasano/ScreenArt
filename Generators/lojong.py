import json
import os
import random
from .text import Text

class Lojong(Text):
    SOURCES = [
        ("lojong_slogans_eng.json", "English"),
        ("lojong_slogans_tib.json", "Tibetan"),
    ]
    COLORS = [
        ("white", "black"), ("yellow", "blue"),
        ("orange", "purple"), ("red", "white"),
        ("green", "white"), ("blue", "white"),
        ("purple", "white"), ("black", "white"),
    ]

    def __init__(self):
        super().__init__()

        lojong_config = self.config.get("lojong", {})
        self.file_count = lojong_config.get("file_count", 3)

        self.out_dir = os.path.join(self.config["paths"]["generators_in"], "lojong")
        os.makedirs(self.out_dir, exist_ok=True)

        input_base_dir = os.path.join(self.base_path, "Generators", "Data", "Lojong")

        # Load both JSON files once at init — they never change at runtime
        self._data: dict[str, list[dict]] = {}
        for filename, language in self.SOURCES:
            path = os.path.join(input_base_dir, filename)
            data = self._load_json(path)
            if data is not None:
                self._data[language] = data
                # Pre-group slogans by point so format_text is O(1) lookup
                self._by_point: dict[str, dict[int, list[dict]]] = {}
                self._by_point[language] = {}
                for slogan in data:
                    pt = slogan.get("point")
                    if pt is not None:
                        self._by_point[language].setdefault(int(pt), []).append(slogan)

        #self.warm_cache()
        self.log.debug(f"Lojong loaded languages: {list(self._data.keys())}")

    def _load_json(self, path: str) -> list | None:
        """Load a JSON file, trying multiple encodings. Returns None on failure."""
        if not os.path.exists(path):
            self.log.debug(f"File not found: {path}")
            return None

        for enc in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "iso-8859-1"):
            try:
                with open(path, encoding=enc, errors="replace") as f:
                    return json.load(f)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                self.log.debug(f"Failed {path!r} with {enc}: {e}")
            except Exception as e:
                self.log.debug(f"Unexpected error {path!r} with {enc}: {e}")

        self.log.critical(f"Could not load {path} with any encoding.")
        return None

    def _format_text(self, slogans: list[dict], point: int) -> list[str]:
        """Return display lines for all slogans belonging to a point."""
        lines = []
        for i, slogan in enumerate(slogans):
            if i == 0:
                category = slogan.get("category", "General")
                lines.append(f"#{point} — {category} —")
            lines.append(slogan.get("text", ""))
        return lines

    def _pick_lines(self, language: str) -> list[str]:
        """Select a random point's slogans; fall back to a random sample."""
        by_point = self._by_point.get(language, {})
        if by_point:
            point = random.choice(list(by_point.keys()))
            return self._format_text(by_point[point], point)

        # Fallback: no point grouping available
        all_slogans = self._data.get(language, [])
        sample = random.sample(all_slogans, min(len(all_slogans), 3))
        return self._format_text(sample, 0)

    def warm_cache(self) -> None:
        """Pre-compute font sizes for all point groups in all languages.
        Call once after adding or changing slogan data.
        """
        self.log.debug("Warming Lojong font size cache...")
        count = 0
        for language, by_point in self._by_point.items():
            font_path = self.language_fonts.get(language, self.language_fonts["English"])
            for point, slogans in by_point.items():
                lines = self._format_text(slogans, point)
                self._find_max_font_size(font_path, lines)
                count += 1
        self.log.debug(f"Lojong cache warmed with {count} entries.")

    def run(self, *args, **kwargs) -> None:
        available = list(self._data.keys())
        if not available:
            self.log.critical("No Lojong data loaded; aborting run.")
            return

        for i in range(self.file_count):
            language = random.choice(available)
            lines = self._pick_lines(language)
            if not lines:
                self.log.debug(f"No lines for {language}, skipping.")
                continue

            bg_color, fg_color = random.choice(self.COLORS)

            img = self.generate_text_image(
                lines_to_draw=lines,
                language=language,
                bg_color=bg_color,
                fg_color=fg_color,
            )

            out_path = os.path.join(self.out_dir, f"lojong_{i}.jpeg")
            try:
                img.convert("RGB").save(out_path, quality=95)
                self.log.debug(f"Saved: {out_path}")
            except Exception as e:
                self.log.debug(f"Failed to save {out_path}: {e}")
