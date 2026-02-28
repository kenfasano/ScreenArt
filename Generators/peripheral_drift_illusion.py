from .drawGenerator import DrawGenerator
from PIL import Image, ImageDraw 
import math
import colorsys
import random
import os

class PeripheralDriftIllusion(DrawGenerator):
    def __init__(self):
        super().__init__()
        self.file_count = self.config.get("file_count", 3)
        self.base_filename = "peripheral_drift"

    def generate_gradient_background(self, width: int, height: int, color_top: tuple[int, int, int], color_bottom: tuple[int, int, int]) -> Image.Image:
        """Generates a vertical gradient background."""
        base = Image.new('RGB', (width, height), color_top)
        top = Image.new('RGB', (width, height), color_bottom)
        mask = Image.new('L', (width, height))
        mask_data = []
        
        for y in range(height):
            alpha: int = int(255 * (y / height))
            mask_data.extend([alpha] * width)
            
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return base

    def create_spinning_optical_illusion(
        self, width: int = 800, height: int = 800,
        num_circles_x: int = 2, num_circles_y: int = 2,
        base_radius: int = 180, num_segments_per_turn: int = 40,
        num_turns: int = 6, spiral_tightness: float = 1.0,
        hue_start_offset: float = 0.0, hue_cycles: float = 2.0,
        bg_color_top: tuple[int, int, int] = (60, 40, 80),
        bg_color_bottom: tuple[int, int, int] = (10, 5, 20)
    ) -> Image.Image:
        
        img = self.generate_gradient_background(width, height, bg_color_top, bg_color_bottom)
        draw = ImageDraw.Draw(img)

        center_x_step: float = width / (num_circles_x + 1) if num_circles_x > 0 else width / 2
        center_y_step: float = height / (num_circles_y + 1) if num_circles_y > 0 else height / 2

        total_segments: int = num_segments_per_turn * num_turns
        gap_per_turn = base_radius / num_turns
        snake_half_width = (gap_per_turn * 0.9) / 2

        for i in range(num_circles_x):
            for j in range(num_circles_y):
                center_x: int = int((i + 1) * center_x_step)
                center_y: int = int((j + 1) * center_y_step)

                for s in range(total_segments):
                    progress: float = s / total_segments
                    next_progress: float = (s + 1) / total_segments
                    
                    angle_start: float = math.radians(s * (360 / num_segments_per_turn))
                    angle_end: float = math.radians((s + 1) * (360 / num_segments_per_turn))

                    r_center_start: float = base_radius * (1 - progress) * spiral_tightness
                    r_center_end: float = base_radius * (1 - next_progress) * spiral_tightness

                    r_outer_start = r_center_start + snake_half_width
                    r_inner_start = max(0, r_center_start - snake_half_width)
                    r_outer_end = r_center_end + snake_half_width
                    r_inner_end = max(0, r_center_end - snake_half_width)
                    
                    current_hue_pos = (hue_start_offset + (progress * hue_cycles)) % 1.0
                    
                    if s % 2 == 0:
                        r, g, b = colorsys.hsv_to_rgb(current_hue_pos, 0.8, 255)
                    else:
                        r, g, b = colorsys.hsv_to_rgb(current_hue_pos, 1.0, 100)
                    
                    segment_color = (int(r), int(g), int(b))

                    x1_out = center_x + r_outer_start * math.cos(angle_start)
                    y1_out = center_y + r_outer_start * math.sin(angle_start)
                    x2_out = center_x + r_outer_end * math.cos(angle_end)
                    y2_out = center_y + r_outer_end * math.sin(angle_end)
                    x2_in = center_x + r_inner_end * math.cos(angle_end)
                    y2_in = center_y + r_inner_end * math.sin(angle_end)
                    x1_in = center_x + r_inner_start * math.cos(angle_start)
                    y1_in = center_y + r_inner_start * math.sin(angle_start)

                    points = [
                        (int(x1_out), int(y1_out)),
                        (int(x2_out), int(y2_out)),
                        (int(x2_in), int(y2_in)),
                        (int(x1_in), int(y1_in))
                    ]
                    draw.polygon(points, fill=segment_color)

        return img

    def run(self, *args, **kwargs):
        with self.timer():
            out_dir = os.path.join(self.config["paths"]["generators_in"], "opticalillusions")
            os.makedirs(out_dir, exist_ok=True)

            for i in range(self.file_count):
                turns: int = 6 + random.randint(1,6)
                hue_offset: float = (i * 0.125 * random.randint(1,7)) % 1.0 
                
                choice = random.randint(1,4)
                img: Image.Image | None = None 

                match choice:
                    case 1:
                        img = self.create_spinning_optical_illusion(
                            width=800, height=800, num_circles_x=2, num_circles_y=2,
                            base_radius=180, num_segments_per_turn=45, num_turns=turns,
                            hue_start_offset=hue_offset, hue_cycles=3.0, 
                            bg_color_top=(50 + (i*20), 20, 60), bg_color_bottom=(10, 5, 15)
                        )
                    case 2:
                        img = self.create_spinning_optical_illusion(
                            width=800, height=800, num_circles_x=2, num_circles_y=2,
                            base_radius=120, num_segments_per_turn=40, num_turns=3,              
                            spiral_tightness=1.0, hue_start_offset=0.0, hue_cycles=2.0,           
                            bg_color_top=(80, 60, 20), bg_color_bottom=(20, 10, 0)
                        )
                    case 3:
                        img = self.create_spinning_optical_illusion(
                            width=800, height=800, num_circles_x=3, num_circles_y=3,
                            base_radius=80, num_segments_per_turn=50, num_turns=4,              
                            spiral_tightness=0.8, hue_start_offset=0.125, hue_cycles=2.0,           
                            bg_color_top=(20, 30, 70), bg_color_bottom=(5, 10, 20)
                        )
                    case 4:
                        img = self.create_spinning_optical_illusion(
                            width=800, height=800, num_circles_x=1, num_circles_y=1,
                            base_radius=250, num_segments_per_turn=60, num_turns=2,              
                            spiral_tightness=1.0, hue_start_offset=0.25, hue_cycles=2.0,           
                            bg_color_top=(70, 20, 20), bg_color_bottom=(20, 5, 5)
                        )

                if img:
                    filename = os.path.join(out_dir, f"{self.base_filename}_{i+1}.jpeg")
                    try:
                        img.save(filename)
                        self.log.debug(f"Saved Optical Illusion: {filename}")
                    except Exception as e:
                        self.log.debug(f"Failed to save {filename}: {e}")
