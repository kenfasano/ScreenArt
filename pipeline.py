import os
import cv2
import random
import numpy as np
from pathlib import Path
from collections import defaultdict

from .screenArt import ScreenArt

class ImageProcessingPipeline(ScreenArt):
    def __init__(self):
        super().__init__("ScreenArt")
        self.out_dir = self.config["paths"]["transformers_out"]
        self.reject_dir = self.config["paths"]["rejected_out"]
        self.accepted = 0
        self.rejected = 0
        self.stats: defaultdict[str, list[float]] = defaultdict(list)

    def run(self, source_dir: str, transformers: list):
        image_files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not image_files:
            self.log.debug(f"No images found in {source_dir} to process.")
            return

        for filename in image_files:
            input_path = os.path.join(source_dir, filename)

            img_bgr = cv2.imread(input_path)
            if img_bgr is None:
                self.log.error(f"Failed to read image: {input_path}")
                continue

            # Convert once to float32 [0, 1] — stays here for entire transformer chain
            img_f32 = img_bgr.astype(np.float32) / 255.0

            for transformer in transformers:
                t_name = transformer.__class__.__name__
                try:
                    with self.timer(custom_name=t_name) as t:
                        img_f32 = transformer.run(img_f32)
                except Exception as e:
                    self.log.error(f"{t_name}: {e}")
                    return
                self.stats[t_name].append(t.elapsed)

            # Convert back once after all transformers are done
            img_out = np.clip(img_f32 * 255.0, 0, 255).astype(np.uint8)

            base_name = Path(filename).stem
            grade = self._calculate_grade(img_out)
            new_filename = f"{base_name}-{grade}.jpeg"
            self._evaluate_and_save(img_out, new_filename, grade)

    def _calculate_grade(self, img_np: np.ndarray) -> str:
        return random.choice(['A', 'B', 'C', 'D', 'F'])

    def _evaluate_and_save(self, img_np: np.ndarray, filename: str, grade: str):
        if grade in ('A', 'B', 'C'):
            final_path = os.path.join(self.out_dir, filename)
            self.accepted += 1
            status = "ACCEPTED"
        else:
            final_path = os.path.join(self.reject_dir, filename)
            self.rejected += 1
            status = "REJECTED"

        cv2.imwrite(final_path, img_np, [cv2.IMWRITE_JPEG_QUALITY, 95])
        self.log.debug(f"[{status} - Grade: {grade}] Saved to: {final_path}")

    def get_accepted_rejected(self) -> str:
        return f"Accepted: {self.accepted}\nRejected: {self.rejected}"

    def get_performance_stats(self) -> dict[str, list[float]]:
        return self.stats
