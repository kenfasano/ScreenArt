import os
import random
import cv2
import numpy as np
from collections import defaultdict
import piexif

from .screenArt import ScreenArt
from .Transformers.RasterTransformers.rasterTransformer import RasterTransformer

class ImageProcessingPipeline(ScreenArt):
    def __init__(self):
        super().__init__("ScreenArt")
        self.out_dir = os.path.expanduser(self.config["paths"]["transformers_out"])
        self.reject_dir = os.path.expanduser(self.config["paths"]["rejected_out"])
        os.makedirs(self.out_dir, exist_ok=True)
        os.makedirs(self.reject_dir, exist_ok=True)
        self.accepted = 0
        self.rejected = 0
        self.stats: defaultdict[str, list[float]] = defaultdict(list)

    def run(self, source_dir: str, transformers: list[RasterTransformer]):
        image_files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not image_files:
            self.log.debug(f"No images found in {source_dir} to process.")
            return

        for filename in image_files:
            # Sample a fresh random subset of transformers for each image
            num_to_pick = random.randint(1, min(4, len(transformers)))
            selected = random.sample(transformers, num_to_pick)

            input_path = os.path.join(source_dir, filename)

            img_bgr = cv2.imread(input_path)
            if img_bgr is None:
                self.log.error(f"Failed to read image: {input_path}")
                continue

            # Convert once to float32 [0, 1] — stays here for entire transformer chain
            img_f32 = img_bgr.astype(np.float32) / 255.0

            metadata_parts: list[str] = []
            for transformer in selected:
                t_name = transformer.__class__.__name__
                try:
                    with self.timer(custom_name=t_name) as t:
                        img_f32 = transformer.run(img_f32)
                    meta = transformer.get_image_metadata()
                    self.log.info(f'"{t_name}","{meta}"')
                    metadata_parts.append(f"{t_name}:{meta}" if meta else t_name)
                except Exception as e:
                    self.log.error(f"{t_name}: {e}")
                    continue
                self.stats[t_name].append(t.elapsed)

            # Convert back once after all transformers are done
            img_out = np.clip(img_f32 * 255.0, 0, 255).astype(np.uint8)
            try:
                self._evaluate_and_save(img_out, filename, metadata_parts)
            except Exception as e:
                self.log.error(f"Failed to save image: {e}")

    def _calculate_grade(self, img_np: np.ndarray) -> str:
        """
        Scores image quality as a composite of sharpness, contrast, and brightness.
        Returns a grade letter: A, B, C, or F.

        - Sharpness:  Laplacian variance on a log scale, bell-curved to prefer
                      natural detail over noise or flat regions.
        - Contrast:   Grayscale std dev, saturating at ~60.
        - Brightness: Penalty multiplier — extreme darks/brights tank the score.
        """
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY).astype(np.float32)

        # Sharpness: log-scaled Laplacian variance, bell curve peaking at ~150
        lap_var = float(cv2.Laplacian(gray, cv2.CV_32F).var())
        log_sharp = np.log1p(lap_var)
        sharpness_score = float(np.exp(-((log_sharp - 5.0) ** 2) / (2 * 3.0 ** 2)))
        if lap_var < 2.0:
            sharpness_score = 0.0  # hard floor: essentially flat image

        # Contrast: std dev, saturates at 60
        contrast_score = float(np.clip(gray.std() / 60.0, 0, 1))

        # Brightness: penalty multiplier, peaks at 128, floor 0.1
        brightness_penalty = max(0.1, 1.0 - abs(float(gray.mean()) - 128) / 128.0)

        # Composite: sharpness-weighted base, scaled by brightness penalty
        score = (sharpness_score * 0.6 + contrast_score * 0.4) * brightness_penalty

        if score >= 0.60:
            return "A"
        elif score >= 0.45:
            return "B"
        elif score >= 0.30:
            return "C"
        else:
            return "F"

    def _evaluate_and_save(self, img_np: np.ndarray, filename: str, metadata_parts: list[str] | None = None):
        grade = self._calculate_grade(img_np)
        stem, ext = os.path.splitext(filename)
        if not ext:
            ext = '.png'
        graded_filename = f"{stem}-{grade}{ext}"

        if grade in ('A', 'B', 'C'):
            final_path = os.path.join(self.out_dir, graded_filename)
            self.accepted += 1
        else:
            final_path = os.path.join(self.reject_dir, graded_filename)
            self.rejected += 1

        if ext.lower() in ('.jpg', '.jpeg'):
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 95]
            cv2.imwrite(final_path, img_np, encode_params)
            # Embed transformer metadata into TIFF ImageDescription (readable by Sandy)
            if metadata_parts:
                description = " | ".join(metadata_parts)
                try:
                    exif_dict = {"0th": {piexif.ImageIFD.ImageDescription: description.encode("utf-8")}}
                    exif_bytes = piexif.dump(exif_dict)
                    piexif.insert(exif_bytes, final_path)
                except Exception as e:
                    self.log.warning(f"Could not write EXIF to {final_path}: {e}")
        else:
            encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
            cv2.imwrite(final_path, img_np, encode_params)

        self.log.info(f"[Grade: {grade}] Saved to: {final_path}")

    def get_accepted_rejected(self) -> str:
        return f"Accepted: {self.accepted}\nRejected: {self.rejected}"

    def get_performance_stats(self) -> dict[str, list[float]]:
        return self.stats
