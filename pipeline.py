import json
import os
import random
import cv2
import numpy as np
from collections import defaultdict

from .screenArt import ScreenArt
from .Transformers.RasterTransformers.rasterTransformer import RasterTransformer

# Maps source_dir folder names to source type keys used in transformer_weights
_SOURCE_TYPE_MAP = {
    "lojong":   "lojong",
    "bible":    "psalms",   # bible generator produces psalms
    "wiki":     "photo",
    "nasa":     "photo",
    "goes":     "photo",
    "maps":     "photo",
    "bubbles":  "bubbles",
    "cubes":    "cubes",
    "hilbert":  "generated",
    "kochsnowflake": "generated",
    "peripheraldriftillusion": "peripheral_drift",
}

def _source_type_from_dir(source_dir: str) -> str:
    """Derive source type key from the last component of the source directory."""
    folder = os.path.basename(os.path.normpath(source_dir)).lower()
    return _SOURCE_TYPE_MAP.get(folder, "photo")


class ImageProcessingPipeline(ScreenArt):
    def __init__(self):
        super().__init__("ScreenArt")
        self.out_dir    = os.path.expanduser(self.config["paths"]["transformers_out"])
        self.reject_dir = os.path.expanduser(self.config["paths"]["rejected_out"])
        os.makedirs(self.out_dir,    exist_ok=True)
        os.makedirs(self.reject_dir, exist_ok=True)
        self.accepted = 0
        self.rejected = 0
        self.stats: defaultdict[str, list[float]] = defaultdict(list)
        self._weight_cache: dict[str, dict[str, float]] = {}  # source_type -> {t_name: weight}

    def _get_transformer_weights(self, source_type: str) -> dict[str, float]:
        """
        Return {transformer_name: weight} for the given source type.
        Looks up config["transformer_weights"], merging "default" with
        source-specific overrides. Results are cached per source_type.
        If transformer_weights is absent or disabled, returns {} (uniform sampling).
        """
        if source_type in self._weight_cache:
            return self._weight_cache[source_type]

        tw = self.config.get("transformer_weights", {})
        if not tw.get("enabled", True):
            self._weight_cache[source_type] = {}
            return {}

        defaults = tw.get("default", {})
        overrides = tw.get(source_type, {})

        # Merge: start with defaults, apply source-specific overrides
        merged = {k.lower(): float(v) for k, v in defaults.items()}
        merged.update({k.lower(): float(v) for k, v in overrides.items()})

        self._weight_cache[source_type] = merged
        return merged

    def _sample_transformers(self,
                              transformers: list[RasterTransformer],
                              source_type: str) -> list[RasterTransformer]:
        """
        Sample 1–4 transformers using per-source weights from config.
        Falls back to uniform random.sample if weights are disabled or missing.
        """
        n = random.randint(1, min(4, len(transformers)))
        weights = self._get_transformer_weights(source_type)

        if not weights:
            return random.sample(transformers, n)

        # Build weight list aligned to the transformer list
        w = [max(weights.get(t.__class__.__name__.lower(), 1.0), 0.0)
             for t in transformers]

        total = sum(w)
        if total <= 0:
            return random.sample(transformers, n)

        # Weighted sampling without replacement
        selected = []
        pool = list(zip(transformers, w))
        for _ in range(n):
            if not pool:
                break
            ts, ws = zip(*pool)
            cum = []
            running = 0.0
            for wt in ws:
                running += wt
                cum.append(running)
            r = random.uniform(0, cum[-1])
            idx = next(i for i, c in enumerate(cum) if c >= r)
            selected.append(ts[idx])
            pool.pop(idx)

        return selected

    def run(self, source_dir: str, transformers: list[RasterTransformer]):
        image_files = [f for f in os.listdir(source_dir)
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not image_files:
            self.log.debug(f"No images found in {source_dir} to process.")
            return

        source_type = _source_type_from_dir(source_dir)
        self.log.debug(f"Pipeline source_type={source_type} for {source_dir}")

        for filename in image_files:
            selected = self._sample_transformers(transformers, source_type)

            input_path = os.path.join(source_dir, filename)
            img_bgr = cv2.imread(input_path)
            if img_bgr is None:
                self.log.error(f"Failed to read image: {input_path}")
                continue

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

            img_out = np.clip(img_f32 * 255.0, 0, 255).astype(np.uint8)
            try:
                self._evaluate_and_save(img_out, filename, source_dir)
            except Exception as e:
                self.log.error(f"Failed to save image: {e}")

    def _calculate_grade(self, img_np: np.ndarray) -> str:
        """
        Scores image quality as a composite of sharpness, contrast, highlights,
        hue diversity, and uniform region detection.
        Returns a grade letter: A, B, C, or F.
        """
        gray    = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY).astype(np.float32)
        lap_var = float(cv2.Laplacian(gray, cv2.CV_32F).var())
        mean    = float(gray.mean())
        std_dev = float(gray.std())

        PEAK = 150.0
        if lap_var < 2.0:
            sharpness = 0.0
        elif lap_var <= PEAK:
            sharpness = ((lap_var - 2.0) / (PEAK - 2.0)) ** 0.7
        else:
            log_ratio = np.log(lap_var / PEAK)
            sharpness = float(np.exp(-0.5 * (log_ratio / 3.0) ** 2))

        contrast = float(np.clip(std_dev / 50.0, 0.0, 1.0))

        if std_dev < 1:
            hi_frac = 1.0 if mean > 220 else 0.0
        else:
            hi_frac = float(0.5 * (1.0 - float(np.tanh((220.0 - mean) / (std_dev * 1.4142)))))
        if hi_frac < 0.15:
            hi_penalty = 1.0
        elif hi_frac > 0.55:
            hi_penalty = 0.55
        else:
            hi_penalty = 1.0 - (hi_frac - 0.15) / 0.40 * 0.45

        is_clipped = (mean < 15 and std_dev < 20) or (mean > 240 and std_dev < 20)
        clip_mult  = 0.35 if is_clipped else 1.0

        score = (sharpness * 0.60 + contrast * 0.40) * clip_mult * hi_penalty

        if std_dev < 25:
            score = min(score, 0.49)

        # --- Hue diversity penalty ---
        # Fires when >80% of vividly-saturated pixels (sat>80) share a single
        # 5° hue bin AND hue std-dev is <12 (truly monochromatic, not biased).
        # Requires 15% vivid pixels to avoid greyscale false positives.
        # Caps at B — catches solid-colour blobs without penalising gradients,
        # dark space images, or naturally hue-biased photos and auroras.
        small = cv2.resize(img_np, (320, 213))
        hsv   = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        vivid_mask  = hsv[:, :, 1] > 80
        vivid_count = int(vivid_mask.sum())
        if vivid_count >= (320 * 213 * 0.15):
            hues = hsv[:, :, 0][vivid_mask]
            counts, _ = np.histogram(hues, bins=36, range=(0, 180))
            dominant_frac = float(counts.max()) / vivid_count
            hue_std = float(hues.std())
            if dominant_frac > 0.80 and hue_std < 12.0:
                score = min(score, 0.49)  # cap at B

        if score >= 0.65:   return "A"
        elif score >= 0.50: return "B"
        elif score >= 0.35: return "C"
        else:               return "F"

    def _evaluate_and_save(self, img_np: np.ndarray, filename: str, source_dir: str):
        grade = self._calculate_grade(img_np)
        stem, ext = os.path.splitext(filename)
        if not ext:
            ext = '.png'

        layout_mode = None
        sidecar_path = os.path.join(source_dir, f"{stem}.json")
        if os.path.exists(sidecar_path):
            try:
                with open(sidecar_path, encoding="utf-8") as sf:
                    layout_mode = json.load(sf).get("layout_mode")
            except Exception as e:
                self.log.debug(f"Could not read sidecar {sidecar_path}: {e}")
            finally:
                try:
                    os.remove(sidecar_path)
                except OSError:
                    pass

        mode_tag = f"-{layout_mode}" if layout_mode else ""
        graded_filename = f"{stem}-{grade}{mode_tag}{ext}"

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
