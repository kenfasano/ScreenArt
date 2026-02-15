from . import drawGenerator
from PIL import Image, ImageDraw #type: ignore
import math
import colorsys
import random
from .. import common

DEFAULT_FILE_COUNT = 3

class PeripheralDriftIllusion(drawGenerator.DrawGenerator):
    def __init__(self, config: dict):
        super().__init__(config, "peripheral_drift_illusion")
        self.file_count = self.config.get("file_count", DEFAULT_FILE_COUNT) if self.config else DEFAULT_FILE_COUNT 
        self.base_filename = "peripheral_drift"

    def generate_gradient_background(self, width: int, height: int, color_top: tuple[int, int, int], color_bottom: tuple[int, int, int]) -> Image.Image:
        """Generates a vertical gradient background."""
        base = Image.new('RGB', (width, height), color_top)
        top = Image.new('RGB', (width, height), color_bottom)
        mask = Image.new('L', (width, height))
        mask_data = []
        
        # Optimization: Create one row and repeat it
        for y in range(height):
            # 0 = Top Color, 255 = Bottom Color
            alpha: int = int(255 * (y / height))
            mask_data.extend([alpha] * width)
            
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return base

    def create_spinning_optical_illusion(
        self,
        width: int = 800,
        height: int = 800,
        num_circles_x: int = 2,
        num_circles_y: int = 2,
        base_radius: int = 180,
        num_segments_per_turn: int = 40,
        num_turns: int = 6,
        spiral_tightness: float = 1.0,
        hue_start_offset: float = 0.0,  # New: Start rainbow anywhere (0.0 - 1.0)
        hue_cycles: float = 2.0,        # New: How many times rainbow repeats
        bg_color_top: tuple[int, int, int] = (60, 40, 80),   # Lighter Purple
        bg_color_bottom: tuple[int, int, int] = (10, 5, 20)  # Deep Dark Purple
    ) -> Image.Image:
        
        # 1. Generate Gradient Background
        img = self.generate_gradient_background(width, height, bg_color_top, bg_color_bottom)
        draw = ImageDraw.Draw(img)

        center_x_step: float = width / (num_circles_x + 1) if num_circles_x > 0 else width / 2
        center_y_step: float = height / (num_circles_y + 1) if num_circles_y > 0 else height / 2

        total_segments: int = num_segments_per_turn * num_turns

        # Calculate Snake Thickness
        # We want the snake to fit `num_turns` inside `base_radius`.
        # Space per turn = base_radius / num_turns.
        # We make the snake 90% of that space so there is a small gap.
        gap_per_turn = base_radius / num_turns
        snake_half_width = (gap_per_turn * 0.9) / 2

        for i in range(num_circles_x):
            for j in range(num_circles_y):
                center_x: int = int((i + 1) * center_x_step)
                center_y: int = int((j + 1) * center_y_step)

                # Draw the spiral segments
                for s in range(total_segments):
                    progress: float = s / total_segments
                    next_progress: float = (s + 1) / total_segments

                    # --- GEOMETRY CORRECTION ---
                    
                    # 1. Current Angle
                    angle_start: float = math.radians(s * (360 / num_segments_per_turn))
                    angle_end: float = math.radians((s + 1) * (360 / num_segments_per_turn))

                    # 2. Center-line Radius (Where the spine of the snake is)
                    # It shrinks as we go in
                    r_center_start: float = base_radius * (1 - progress) * spiral_tightness
                    r_center_end: float = base_radius * (1 - next_progress) * spiral_tightness

                    # 3. Inner and Outer Edges (Ribbon Width)
                    # We add/subtract width from the center line
                    r_outer_start = r_center_start + snake_half_width
                    r_inner_start = r_center_start - snake_half_width
                    
                    r_outer_end = r_center_end + snake_half_width
                    r_inner_end = r_center_end - snake_half_width

                    # Safety: Don't draw negative radius
                    if r_inner_start < 0: 
                        r_inner_start = 0
                    if r_inner_end < 0: 
                        r_inner_end = 0

                    # --- COLOR LOGIC ---
                    
                    # Cycle hue based on progress + offset
                    current_hue_pos = (hue_start_offset + (progress * hue_cycles)) % 1.0
                    
                    # Alternating Pattern for Illusion (A-B-C-D sequence works best)
                    # Here we stick to Bright/Dark alternation for simplicity
                    if s % 2 == 0:
                        # Bright
                        r, g, b = colorsys.hsv_to_rgb(current_hue_pos, 0.8, 255)
                    else:
                        # Dark / Shadow
                        r, g, b = colorsys.hsv_to_rgb(current_hue_pos, 1.0, 100)
                    
                    segment_color = (int(r), int(g), int(b))

                    # --- DRAWING ---
                    
                    # Calculate 4 points of the ribbon segment
                    x1_out = center_x + r_outer_start * math.cos(angle_start)
                    y1_out = center_y + r_outer_start * math.sin(angle_start)
                    
                    x2_out = center_x + r_outer_end * math.cos(angle_end)
                    y2_out = center_y + r_outer_end * math.sin(angle_end)
                    
                    x2_in = center_x + r_inner_end * math.cos(angle_end)
                    y2_in = center_y + r_inner_end * math.sin(angle_end)
                    
                    x1_in = center_x + r_inner_start * math.cos(angle_start)
                    y1_in = center_y + r_inner_start * math.sin(angle_start)

                    points: list[tuple[int, int]] = [
                        (int(x1_out), int(y1_out)),
                        (int(x2_out), int(y2_out)),
                        (int(x2_in), int(y2_in)),
                        (int(x1_in), int(y1_in))
                    ]
                    
                    draw.polygon(points, fill=segment_color)

        return img

    def draw(self):
        for i in range(self.file_count):
            # Vary turns and rainbow start per image
            turns: int = 6 + random.randint(1,6)
            hue_offset: float = (i * 0.125 * random.randint(1,7)) % 1.0 # 0.25: 0.0, 0.25, 0.5, 0.75
            
            # Select a random case
            choice = random.randint(1,4)
            
            # Use 'img = None' to ensure it's initialized
            img: Image.Image | None = None 

            match choice:
                case 1:
                    # This case was already correct
                    img = self.create_spinning_optical_illusion(
                        width=800,
                        height=800,
                        num_circles_x=2,
                        num_circles_y=2,
                        base_radius=180,
                        num_segments_per_turn=45,
                        num_turns=turns,
                        hue_start_offset=hue_offset,
                        hue_cycles=3.0, # Rainbow repeats 3 times
                        bg_color_top=(50 + (i*20), 20, 60), # Vary background slightly
                        bg_color_bottom=(10, 5, 15)
                    )

                case 2:
                    # FIXED: Mapped old params to new signature
                    # Original had gold/brown colors; now uses rainbow
                    img = self.create_spinning_optical_illusion(
                        width=800,
                        height=800,
                        num_circles_x=2,
                        num_circles_y=2,
                        base_radius=120,
                        num_segments_per_turn=40, # from num_segments
                        num_turns=3,              # from num_inner_spirals
                        spiral_tightness=1.0,
                        hue_start_offset=0.0,     # from angle_offset_deg=0
                        hue_cycles=2.0,           # Default
                        bg_color_top=(80, 60, 20),# Gold/Brown background
                        bg_color_bottom=(20, 10, 0)
                    )

                case 3:
                    # FIXED: Mapped old params to new signature
                    # Original had blue colors; now uses rainbow on blue bg
                    img = self.create_spinning_optical_illusion(
                        width=800,
                        height=800,
                        num_circles_x=3,
                        num_circles_y=3,
                        base_radius=80,
                        num_segments_per_turn=50, # from num_segments
                        num_turns=4,              # from num_inner_spirals
                        spiral_tightness=0.8,
                        hue_start_offset=0.125,   # from angle_offset_deg=45 (45/360)
                        hue_cycles=2.0,           # Default
                        bg_color_top=(20, 30, 70),# Blueish background
                        bg_color_bottom=(5, 10, 20)
                    )

                case 4:
                    # FIXED: Mapped old params to new signature
                    # Original had red colors; now uses rainbow on red bg
                    img = self.create_spinning_optical_illusion(
                        width=800,
                        height=800,
                        num_circles_x=1,
                        num_circles_y=1,
                        base_radius=250,
                        num_segments_per_turn=60, # from num_segments
                        num_turns=2,              # from num_inner_spirals
                        spiral_tightness=1.0,
                        hue_start_offset=0.25,    # from angle_offset_deg=90 (90/360)
                        hue_cycles=2.0,           # Default
                        bg_color_top=(70, 20, 20),# Redish background
                        bg_color_bottom=(20, 5, 5)
                    )

            # Save the image if one was created
            if img:
                this_filename: str = f"{self.paths["generators_in"]}/OpticalIllusions/{self.base_filename}{i+1}.jpeg"
                img.save(this_filename, 'JPEG')
