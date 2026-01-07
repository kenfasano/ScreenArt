from abc import abstractmethod
import random
import sys
from PIL import Image, ImageDraw, ImageFont #type: ignore

# --- Imports from uploaded files ---
# NOTE: These imports assume text.py is placed in the same directory 
# or a directory structure where it can access drawGenerator, common, etc.
from . import drawGenerator 
from .. import log

# --- Configuration Defaults ---
WIDTH: int = 1920
HEIGHT: int = 1280
MIN_FONT_SIZE: int = 20
WIDTH = 1920 
HEIGHT = 1080 
BORDER_SIZE = 15
USABLE_WIDTH = WIDTH - (2 * BORDER_SIZE)
USABLE_HEIGHT = HEIGHT - (2 * BORDER_SIZE)

class Text(drawGenerator.DrawGenerator):
    def __init__(
            self, 
            input_file_paths: list[str],
            output_file_paths: list[str],
            config,
            languages: list[str]):
    
        super().__init__()

        if not input_file_paths or not output_file_paths:
            log.critical(f"{input_file_paths=}, {output_file_paths=}")
            return

        random.seed()

        self.input_file_paths = input_file_paths
        self.output_file_paths = output_file_paths
        self.config = config
        self.languages = languages

        self.current_list: list[str] = []

    def draw_text(self, 
                  drawing: ImageDraw.ImageDraw, 
                  foreground_color: str,
                  lines_to_draw: list[str],
                  language: str):

        y_position = 0

        language_fonts = {
                "Tibetan": "/Users/kenfasano/Library/Fonts/NotoSerifTibetan-VariableFont_wght.ttf",
                "Hebrew": "/System/Library/Fonts/ArialHB.ttc",
                "English": "/System/Library/Fonts/Supplemental/Arial.ttf"
                }

        try:
            language_font = language_fonts.get(language, language_fonts["English"]) 
            # The 'lines' variable is correctly passed as list[dict] here:
            max_font_size, lines_to_draw = self.get_max_font_size(language_font, lines_to_draw)
            font = ImageFont.truetype(language_font, max_font_size)
        except IOError:
            font = ImageFont.load_default()
            log.critical("Truetype font loading failed.")
            return # Exit early if font fails, to prevent further errors

        for i, sentence in enumerate(lines_to_draw):
            # 3. Get Text Height for spacing calculation
            text_height = 0
            try:
                text_bbox = drawing.textbbox((0, 0), str(sentence), font=font)
                text_height = text_bbox[3] - text_bbox[1]
            except AttributeError:
                _ , text_height = drawing.textsize(sentence, font=font)

            # 4. Draw the text
            drawing.text((10, y_position), sentence, fill=foreground_color, font=font)

            # 5. Calculate Y position for the next line
            # Spacing logic: current text height + half of that for spacing
            line_spacing = text_height + (text_height // 2) 
            y_position += line_spacing

            # Add extra space after the main title/explanation
            if i == 0:
                y_position += 15

            if y_position >= HEIGHT - 50:
                return

    @abstractmethod
    def load_list(self, i: int):
        ...

    def draw(self):
        """
        Creates an image with the given text saves it as a JPEG.
        This overrides the original random sentence generation with fixed text.
        """

        colors: list[tuple[str, str]] = [
                ("white", "black"),
                ("yellow", "blue"),
                ("orange", "purple"),
                ("red", "white"),
                ("green", "white"),
                ("blue", "white"),
                ("purple", "white"),
                ("black", "white")
        ]

        for i in range(len(self.input_file_paths)):
            background_color, foreground_color = random.choice(colors)

            # Create a new blank image
            img: Image.Image = Image.new('RGB', (WIDTH, HEIGHT), background_color)
            drawing: ImageDraw.ImageDraw = ImageDraw.Draw(img)
            self.load_list(i)

            if not self.current_list:
                log.error("self.current_list is empty, skipping image generation.")
                continue

            # FIX 1: Handle Language Selection Safely
            # Lojong passes an empty list for languages, so we must check attributes or default.
            if i < len(self.languages):
                current_lang = self.languages[i]
            elif hasattr(self, 'language'):
                current_lang = self.language
            else:
                current_lang = "English"

            self.draw_text(drawing, foreground_color, self.current_list, current_lang) 
            
            # Save the image as a JPEG file
            try:
                # FIX 2: Handle Output Path Index Error
                # Lojong defines 2 inputs but only 1 output path. This prevents a crash on the second loop.
                if i >= len(self.output_file_paths):
                    log.error(f"Skipping save for image {i}: No corresponding output file path provided.")
                    continue

                img.save(self.output_file_paths[i], 'JPEG')
            except Exception as e:
                log.critical(f"Failed to save image {self.output_file_paths[i]}: {e}")

                sys.exit(1)

    def get_text_size(self, drawing: ImageDraw.ImageDraw, text_lines: list[str], font: ImageFont.ImageFont):
        """Calculates the total size (width and height) of all text lines."""
        total_height = 0
        max_width = 0

        for sentence in text_lines:
            # Use textbbox for more accurate size calculation
            text_bbox = drawing.textbbox((0, 0), sentence, font=font)
            text_height = text_bbox[3] - text_bbox[1]
            text_width = text_bbox[2] - text_bbox[0]

            max_width = max(max_width, text_width)

            # Spacing logic: current text height + half of that for spacing
            line_spacing = text_height + (text_height // 2)
            total_height += line_spacing

        if len(text_lines) > 0:
            pass 

        return max_width, total_height

    def find_max_size_for_block(self, lines: list[str], font_path: str) -> int:
        """Binary search to find max font size for a given block of text."""
        # Use a dummy image for ImageDraw/font measurement
        dummy_img = Image.new('RGB', (1, 1), 'white')
        drawing = ImageDraw.Draw(dummy_img)

        low = 1
        high = 500  # Start with a very large maximum possible font size
        max_size = 0

        # Initialize font outside the loop to satisfy the linter
        font = ImageFont.load_default(1)

        while low <= high:
            mid = (low + high) // 2

            # Load the font for the current trial size
            try:
                font = ImageFont.truetype(font_path, mid)
            except IOError:
                # Fallback if the specific font isn't available
                font = ImageFont.load_default(mid)

            width, height = self.get_text_size(drawing, lines, font)

            if width <= USABLE_WIDTH and height <= USABLE_HEIGHT:
                # Font fits, try a larger size
                max_size = mid
                low = mid + 1
            else:
                # Font is too large, try a smaller size
                high = mid - 1

        return max_size

    def get_max_font_size(self, 
                          font_path: str,
                          text_list: list[str],
                          min_font_size: int = MIN_FONT_SIZE) -> tuple[int, list[str]]:
        """
        Calculates the maximum font size that fits the text within a 1920x1080 image 
        with 15pt border (1890x1050 usable area).
        """
        
        if not text_list:
             log.error("No text lines extracted from input list. Cannot determine max font size.")
             return 10, ["Error: No text loaded or parsed incorrectly."]

        max_size_full = self.find_max_size_for_block(text_list, font_path)

        if max_size_full >= min_font_size:
            return max_size_full, text_list 

        # 2. If full text is too small, split and test half
        split_point = len(text_list) // 2
        half_text_lines = text_list[split_point:] 

        max_size_half = self.find_max_size_for_block(half_text_lines, font_path)

        if max_size_half >= min_font_size:
            return max_size_half, half_text_lines
        else:
            return max_size_full, text_list
