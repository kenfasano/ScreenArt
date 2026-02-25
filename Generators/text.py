# Generators/text.py
import random
from PIL import Image, ImageDraw, ImageFont # type: ignore
from typing import Tuple
import os

# Inherit from your new DrawGenerator utility class
from .drawGenerator import DrawGenerator

class Text(DrawGenerator):
    """
    A specialized utility Generator for drawing text on images.
    Provides canvas creation, dynamic font scaling, and text wrapping.
    """
    def __init__(self):
        super().__init__()
        
        # Pull canvas dimensions from config, falling back to your standard 1080p defaults
        self.width = self.config.get("canvas_width", 1920)
        self.height = self.config.get("canvas_height", 1080)
        self.border_size = self.config.get("border_size", 15)
        self.min_font_size = self.config.get("min_font_size", 20)
        
        self.usable_width = self.width - (2 * self.border_size)
        self.usable_height = self.height - (2 * self.border_size)

        self._setup_fonts()

    def _setup_fonts(self):
        """Maps font paths based on the current operating system."""
        if self.os_type == "darwin":
            # macOS Font Paths
            self.language_fonts = {
                "Tibetan": os.path.expanduser("~/Library/Fonts/NotoSerifTibetan-VariableFont_wght.ttf"),
                "Hebrew": "/System/Library/Fonts/ArialHB.ttc",
                "English": "/System/Library/Fonts/Supplemental/Arial.ttf"
            }
        else:
            # Linux (Fedora) Font Paths - Update these to match your Linux font directory
            self.language_fonts = {
                # Replace the string below with the exact Jomolhari path you found
                "Tibetan": "/usr/share/fonts/jomolhari-fonts/Jomolhari-alpha3c-0605331.ttf",
                "Hebrew": "/usr/share/fonts/google-noto-vf/NotoSansHebrew[wght].ttf",
                "English": "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"
            }

    def generate_text_image(self, 
                            lines_to_draw: list[str], 
                            language: str = "English",
                            bg_color: str = "black", 
                            fg_color: str = "white") -> Image.Image:
        """
        The core utility: Creates an image, scales the font, and draws the text.
        Returns the PIL Image object so the caller (Bible/Lojong) can save it.
        """
        img = Image.new('RGB', (self.width, self.height), bg_color)
        drawing = ImageDraw.Draw(img)

        font_path = self.language_fonts.get(language, self.language_fonts["English"])
        
        # Scale the font to fit the canvas
        max_font_size, lines_to_draw = self.get_max_font_size(font_path, lines_to_draw)
        
        try:
            font = ImageFont.truetype(font_path, max_font_size)
        except IOError:
            self.log.error(f"Failed to load font {font_path}. Using default.")
            font = ImageFont.load_default()

        y_position = self.border_size

        for i, sentence in enumerate(lines_to_draw):
            text_height = 0
            try:
                text_bbox = drawing.textbbox((0, 0), str(sentence), font=font)
                text_height = text_bbox[3] - text_bbox[1]
            except AttributeError:
                _, text_height = drawing.textsize(sentence, font=font)

            # Draw the text with a left margin padding
            drawing.text((self.border_size + 10, y_position), sentence, fill=fg_color, font=font)

            line_spacing = text_height + (text_height // 2) 
            y_position += line_spacing

            # Add extra space after the main title/explanation
            if i == 0:
                y_position += 15

            if y_position >= self.height - 50:
                self.log.warning("Text exceeded canvas height: {text_height=}, {y_position=}")
                break
                
        return img

    def get_max_font_size(self, font_path: str, text_list: list[str]) -> Tuple[int, list[str]]:
        """Calculates the maximum font size that fits the text within the usable area."""
        if not text_list:
             self.log.error("No text lines provided to font scaler.")
             return 10, ["Error: No text loaded."]

        max_size_full = self._find_max_size_for_block(text_list, font_path)

        if max_size_full >= self.min_font_size:
            return max_size_full, text_list 

        # If full text is too small, split and test half
        split_point = len(text_list) // 2
        half_text_lines = text_list[split_point:] 

        max_size_half = self._find_max_size_for_block(half_text_lines, font_path)

        if max_size_half >= self.min_font_size:
            return max_size_half, half_text_lines
        else:
            return max_size_full, text_list

    def _find_max_size_for_block(self, lines: list[str], font_path: str) -> int:
        """Binary search to find max font size for a given block of text."""
        dummy_img = Image.new('RGB', (1, 1), 'white')
        drawing = ImageDraw.Draw(dummy_img)

        low = 1
        high = 500  
        max_size = 0

        while low <= high:
            mid = (low + high) // 2
            try:
                font = ImageFont.truetype(font_path, mid)
            except IOError:
                font = ImageFont.load_default()

            width, height = self._get_text_size(drawing, lines, font)

            if width <= self.usable_width and height <= self.usable_height:
                max_size = mid
                low = mid + 1
            else:
                high = mid - 1

        return max_size

    def _get_text_size(self, drawing: ImageDraw.ImageDraw, text_lines: list[str], font: ImageFont.ImageFont):
        """Calculates the total size (width and height) of all text lines."""
        total_height = 0
        max_width = 0

        for sentence in text_lines:
            text_bbox = drawing.textbbox((0, 0), sentence, font=font)
            text_height = text_bbox[3] - text_bbox[1]
            text_width = text_bbox[2] - text_bbox[0]

            max_width = max(max_width, text_width)
            line_spacing = text_height + (text_height // 2)
            total_height += line_spacing

        return max_width, total_height
        
    # We leave the run() method unimplemented here. Bible and Lojong will provide it.
