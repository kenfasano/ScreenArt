import numpy as np
from .rasterTransformer import RasterTransformer

DEFAULT_DOT_SIZE = 3

class HalftoneTransformer(RasterTransformer):
    """
    Applies a halftone or print-style effect to an image.
    """
    def __init__(self):
        super().__init__()

    def run(self, img_np: np.ndarray, *args, **kwargs) -> np.ndarray:
        t_config = self.config.get("halftonetransformer", {})
       
        dot_size = t_config.get("dot_size", DEFAULT_DOT_SIZE)
        self.dot_size = max(1, dot_size)
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["size"] = self.dot_size

        # Convert to grayscale to determine luminosity
        if img_np.ndim == 3:
            grayscale_np = np.dot(img_np[...,:3], [0.299, 0.587, 0.114])
        else:
            grayscale_np = img_np
            
        height, width = grayscale_np.shape
        step = self.dot_size

        trimmed_height = height - (height % step)
        trimmed_width = width - (width % step)
        grayscale_trimmed = grayscale_np[:trimmed_height, :trimmed_width]

        reshaped_blocks = grayscale_trimmed.reshape(trimmed_height // step, step, trimmed_width // step, step)
        blocks_transposed = reshaped_blocks.transpose(0, 2, 1, 3)

        avg_luminosity = blocks_transposed.mean(axis=(-2, -1))

        # Quantize the average luminosity values
        scaled_luminosity = (avg_luminosity / 255.0 * 4).astype(int)
        new_values = scaled_luminosity * (255.0 / 4)

        new_values_reshaped = new_values[:, :, np.newaxis, np.newaxis]
        output_blocks = np.tile(new_values_reshaped, (1, 1, step, step))

        output_np = output_blocks.transpose(0, 2, 1, 3).reshape(trimmed_height, trimmed_width)

        final_output = np.zeros_like(img_np)
        if img_np.ndim == 3:
            final_output[:trimmed_height, :trimmed_width, 0] = output_np
            final_output[:trimmed_height, :trimmed_width, 1] = output_np
            final_output[:trimmed_height, :trimmed_width, 2] = output_np
        else:
            final_output[:trimmed_height, :trimmed_width] = output_np

        return final_output.astype(np.uint8)
