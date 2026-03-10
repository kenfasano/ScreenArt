import os
import random
import cv2
import numpy as np
from collections import defaultdict

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

            for transformer in selected:
                t_name = transformer.__class__.__name__
                try:
                    with self.timer(custom_name=t_name) as t:
                        img_f32 = transformer.run(img_f32)
                    self.log.info(f'"{t_name}","{transformer.get_image_metadata()}"')
                except Exception as e:
                    self.log.error(f"{t_name}: {e}")
                    continue
                self.stats[t_name].append(t.elapsed)

            # Convert back once after all transformers are done
            img_out = np.clip(img_f32 * 255.0, 0, 255).astype(np.uint8)
            try:
                self._evaluate_and_save(img_out, filename)
            except Exception as e:
                self.log.error(f"Failed to save image: {e}")

    def _calculate_grade(self, img_np: np.ndarray) -> str:
        """
        Scores image quality as a composite of sharpness, contrast, and highlights.
        Returns a grade letter: A, B, C, or F.

        - Sharpness:  Laplacian variance, linear ramp up to peak=150, then gentle
                      log-bell decay (sigma=3.0) — very high lap_var is always good.
        - Contrast:   Grayscale std dev, saturating at 50.
        - Highlights: Estimates fraction of near-white pixels (>220/255). Images
                      dominated by white are penalised even when contrast is high.
        - Clip guard: Genuinely empty images (solid black/white, std<20) get 0.35x.
        - Low-contrast cap: std<25 caps score at 0.49 (prevents sparse line art
                      from scoring A on sharpness alone).
        """
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY).astype(np.float32)
        lap_var = float(cv2.Laplacian(gray, cv2.CV_32F).var())
        mean    = float(gray.mean())
        std_dev = float(gray.std())

        # Sharpness: linear ramp to PEAK, then gentle log-bell decay
        PEAK = 150.0
        if lap_var < 2.0:
            sharpness = 0.0
        elif lap_var <= PEAK:
            sharpness = ((lap_var - 2.0) / (PEAK - 2.0)) ** 0.7
        else:
            log_ratio = np.log(lap_var / PEAK)
            sharpness = float(np.exp(-0.5 * (log_ratio / 3.0) ** 2))

        # Contrast: std dev saturates at 50
        contrast = float(np.clip(std_dev / 50.0, 0.0, 1.0))

        # Highlights penalty: estimate fraction of pixels above 220
        # High highlight fraction = composition dominated by white → penalise
        if std_dev < 1:
            hi_frac = 1.0 if mean > 220 else 0.0
        else:
            # Gaussian CDF approximation: fraction above threshold
            hi_frac = float(0.5 * (1.0 - float(np.tanh((220.0 - mean) / (std_dev * 1.4142)))))
        if hi_frac < 0.15:
            hi_penalty = 1.0
        elif hi_frac > 0.55:
            hi_penalty = 0.55
        else:
            hi_penalty = 1.0 - (hi_frac - 0.15) / 0.40 * 0.45

        # Clip guard: nearly solid black or white images
        is_clipped = (mean < 15 and std_dev < 20) or (mean > 240 and std_dev < 20)
        clip_mult  = 0.35 if is_clipped else 1.0

        score = (sharpness * 0.60 + contrast * 0.40) * clip_mult * hi_penalty

        # Low-contrast cap: sparse lineart or flat images can't reach A on sharpness alone
        if std_dev < 25:
            score = min(score, 0.49)

        if score >= 0.65:
            return "A"
        elif score >= 0.50:
            return "B"
        elif score >= 0.35:
            return "C"
        else:
            return "F"

    def _evaluate_and_save(self, img_np: np.ndarray, filename: str):
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
        else:
            encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 3]

        cv2.imwrite(final_path, img_np, encode_params)
        self.log.info(f"[Grade: {grade}] Saved to: {final_path}")

    def get_accepted_rejected(self) -> str:
        return f"Accepted: {self.accepted}\nRejected: {self.rejected}"

    def get_performance_stats(self) -> dict[str, list[float]]:
        return self.stats
