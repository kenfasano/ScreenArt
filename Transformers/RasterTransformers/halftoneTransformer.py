import numpy as np
import random
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
       
        dot_size = t_config.get("dot_size")
        if not isinstance(dot_size, int):
            dot_size = random.randint(4, 12)
        self.dot_size = max(2, dot_size)
        
        # --- POPULATE METADATA ---
        self.metadata_dictionary["size"] = self.dot_size

        # Convert to grayscale. Input is float32 [0,1]; scale to [0,255] for quantization.
        img_255 = np.clip(img_np, 0.0, 1.0) * 255.0
        if img_np.ndim == 3:
            grayscale_np = np.dot(img_255[...,:3], [0.299, 0.587, 0.114])
        else:
            grayscale_np = img_255
            
        height, width = grayscale_np.shape
        step = self.dot_size

        trimmed_height = height - (height % step)
        trimmed_width = width - (width % step)
        grayscale_trimmed = grayscale_np[:trimmed_height, :trimmed_width]

        reshaped_blocks = grayscale_trimmed.reshape(trimmed_height // step, step, trimmed_width // step, step)
        blocks_transposed = reshaped_blocks.transpose(0, 2, 1, 3)

        avg_luminosity = blocks_transposed.mean(axis=(-2, -1))

        # Quantize the average luminosity values (8 levels → smoother gradients)
        scaled_luminosity = (avg_luminosity / 255.0 * 8).astype(int)
        new_values = scaled_luminosity * (255.0 / 8)

        new_values_reshaped = new_values[:, :, np.newaxis, np.newaxis]
        output_blocks = np.tile(new_values_reshaped, (1, 1, step, step))

        output_np = output_blocks.transpose(0, 2, 1, 3).reshape(trimmed_height, trimmed_width)

        # Fill full canvas — repeat last row/col instead of leaving black borders
        final_output = np.zeros_like(img_np)
        if img_np.ndim == 3:
            for c in range(img_np.shape[2]):
                final_output[:trimmed_height, :trimmed_width, c] = output_np
                if trimmed_width < width:
                    final_output[:trimmed_height, trimmed_width:, c] = output_np[:, -1:]
                if trimmed_height < height:
                    final_output[trimmed_height:, :, c] = final_output[trimmed_height-1:trimmed_height, :, c]
        else:
            final_output[:trimmed_height, :trimmed_width] = output_np
            if trimmed_width < width:
                final_output[:trimmed_height, trimmed_width:] = output_np[:, -1:]
            if trimmed_height < height:
                final_output[trimmed_height:, :] = final_output[trimmed_height-1:trimmed_height, :]

        return np.clip(final_output / 255.0, 0.0, 1.0).astype(np.float32)  # back to [0,1]
