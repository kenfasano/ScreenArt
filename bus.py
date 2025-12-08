import os
import random
import subprocess
import time
from . import common
from . import log

from pathlib import Path
from timeit import timeit
from typing import Callable, Any, Optional, List, Tuple
from collections import defaultdict 
from datetime import datetime

import numpy as np  #type: ignore
import cv2 #type: ignore
from skimage.color import rgb2hsv # type: ignore
from multiprocessing import Pool
from functools import partial
import sys
import json 

from .pipeline import Pipeline

# --- Constants for Analysis ---
NUM_CORES: int = 4
NUM_HUE_BUCKETS: int = 36 
NUM_LUMA_BUCKETS: int = 20

# Thresholds (0-255 scaled or 0.0-1.0 depending on library)
# OpenCV HSV ranges: H:0-179, S:0-255, V:0-255
SAT_THRESH_CV2: float = 0.03 * 255  # ~7.65
VAL_THRESH_CV2: float = 0.05 * 255  # ~12.75

REJECTION_THRESHOLD_PERCENT: float = 75.0

# --- End Constants ---

def _process_chunk(rgb_chunk: np.ndarray, num_buckets: int) -> np.ndarray:
    try:
        # scikit-image rgb2hsv returns floats 0.0-1.0
        hsv_chunk: np.ndarray = rgb2hsv(rgb_chunk)
        hue: np.ndarray = hsv_chunk[..., 0]        
        saturation: np.ndarray = hsv_chunk[..., 1] 
        value: np.ndarray = hsv_chunk[..., 2]      

        # Filter: Must be Saturated AND Bright enough
        mask: np.ndarray = (saturation > 0.03) & (value > 0.05)
        chromatic_hues: np.ndarray = hue[mask]

        if chromatic_hues.size == 0:
            return np.zeros(num_buckets, dtype=np.int64)

        bins: np.ndarray = np.linspace(0.0, 1.0, num_buckets + 1)
        hist, _ = np.histogram(chromatic_hues, bins=bins) 

        return hist.astype(np.int64)
    except Exception as e:
        print(f"Error processing chunk: {e}", file=sys.stderr)
        return np.zeros(num_buckets, dtype=np.int64)

class ImageProcessingBus:
    def __init__(self, output_transformed_dir: str, output_rejected_dir: str):
        self.output_transformed_dir = output_transformed_dir
        self.output_rejected_dir = output_rejected_dir
        self.image_metadata: str = "" 
        self._accepted: int = 0
        self._rejected: int = 0
        self.transformer_times: defaultdict[str, list[float]] = defaultdict(list)

    @timeit # type: ignore
    def apply(self, config: dict, img: Any, transformer: Any):
        processed_img = img.copy()
        try:
            # Capture timing specifically for the transformer logic
            start_ts = time.perf_counter()
            t_name = transformer.__class__.__name__

            processed_img = transformer.apply(config, img)
            desc = "N/A"
            if hasattr(transformer, "get_image_metadata"):
                desc = transformer.get_image_metadata()
            if not desc or desc == "N/A":
                desc = transformer.__class__.__name__
            
            if self.image_metadata:
                self.image_metadata += f"; {self.transformer_name}:{desc}" 
            else:
                self.image_metadata = f"{self.transformer_name}:{desc}"

            end_ts = time.perf_counter()
            
            # Record the duration
            self.transformer_times[t_name].append(end_ts - start_ts)

        except Exception as e:
            log.error(f"Error in {transformer.__class__.__name__}: {e}")      
        return processed_img, self

    def get_performance_stats(self) -> List[Tuple[str, float]]:
        """
        Calculates average run times per transformer.
        Returns:
            A list of tuples (transformer_name, average_seconds),
            sorted by average time in descending order.
        """
        if not self.transformer_times:
            return []

        stats = []
        for name, times in self.transformer_times.items():
            if times:
                avg_time = sum(times) / len(times)
                stats.append((name, avg_time))
        
        # Sort descending by average time
        stats.sort(key=lambda x: x[1], reverse=True)
        return stats

    def analyze_image_hues_from_data(self, img_np_bgr: np.ndarray) -> Optional[np.ndarray]:
        try:
            img_np_rgb = cv2.cvtColor(img_np_bgr, cv2.COLOR_BGR2RGB)
            image_data: np.ndarray = img_np_rgb.astype(np.float32) / 255.0
            
            if image_data.size == 0: return None

            chunks: List[np.ndarray] = np.array_split(image_data, NUM_CORES, axis=0)
            worker_func = partial(_process_chunk, num_buckets=NUM_HUE_BUCKETS)

            results: List[np.ndarray]
            with Pool(processes=NUM_CORES) as pool:
                results = pool.map(worker_func, chunks)

            total_histogram: np.ndarray = np.sum(results, axis=0)
            return total_histogram
        except Exception as e:
            log.error(f"Error during hue analysis: {e}")
            return None

    def analyze_image_luminance(self, img_np_bgr: np.ndarray) -> Optional[np.ndarray]:
        """Calculates histogram for grayscale/luminance distribution."""
        try:
            gray = cv2.cvtColor(img_np_bgr, cv2.COLOR_BGR2GRAY)
            # Calculate histogram with 20 bins (0-255 range)
            hist = cv2.calcHist([gray], [0], None, [NUM_LUMA_BUCKETS], [0, 256])
            return hist.flatten().astype(np.int64)
        except Exception as e:
            log.error(f"Error during luminance analysis: {e}")
            return None

    def check_is_grayscale(self, img_np_bgr: np.ndarray) -> bool:
        """
        Determines if an image should be treated as Grayscale.
        It checks if significant color saturation exists.
        Returns True if colored pixels are < 1% of total.
        """
        try:
            # Resize for speed (100x100 is sufficient for global stats)
            small = cv2.resize(img_np_bgr, (100, 100), interpolation=cv2.INTER_NEAREST)
            hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
            
            # S channel is index 1, V channel is index 2
            s = hsv[:,:,1]
            v = hsv[:,:,2]
            
            # Count pixels that are Saturated AND Bright (not black)
            # OpenCV uses 0-255 range for S and V
            colored_pixels_mask = (s > SAT_THRESH_CV2) & (v > VAL_THRESH_CV2)
            colored_count = np.count_nonzero(colored_pixels_mask)
            total_count = small.shape[0] * small.shape[1]
            
            percent_colored = colored_count / total_count
            return percent_colored < 0.01 # Less than 1% color = Grayscale
            
        except Exception:
            return False # Assume color on error

    def _get_analysis_verdict(self, img_np_bgr: np.ndarray) -> Tuple[bool, str, float, str]:
        # FIX: Removed 'unique_colors' logic entirely.
        # Now strictly uses Saturation check.
        is_grayscale_mode = self.check_is_grayscale(img_np_bgr)
        
        histogram = None
        mode_label = ""
        
        if is_grayscale_mode:
            mode_label = "Luma"
            histogram = self.analyze_image_luminance(img_np_bgr)
        else:
            mode_label = "Hue"
            histogram = self.analyze_image_hues_from_data(img_np_bgr)

        if histogram is None:
            return True, "Analysis failed.", 100.0, mode_label

        total_pixels: np.int64 = np.sum(histogram)
        
        if total_pixels == 0:
            return True, "Image is empty or too dark.", 100.0, mode_label

        percentages: np.ndarray = (histogram / total_pixels) * 100.0
        max_percentage: np.float64 = np.max(percentages)
        
        dominance_value = float(max_percentage)
        
        # Adjacent Bucket Check (Hue Mode Only)
        if not is_grayscale_mode:
            max_adjacent_sum = 0.0
            for i in range(NUM_HUE_BUCKETS):
                next_i = (i + 1) % NUM_HUE_BUCKETS 
                adjacent_sum = percentages[i] + percentages[next_i]
                if adjacent_sum > max_adjacent_sum:
                    max_adjacent_sum = adjacent_sum
            
            dominance_value = max(dominance_value, float(max_adjacent_sum))

        reason = f"{dominance_value:.1f}% max dominance in {mode_label}."
        is_rejected = dominance_value > REJECTION_THRESHOLD_PERCENT

        return is_rejected, reason, dominance_value, mode_label

    def write_exif(self, file_path: str, stem: str, grade: str, image_metadata: str):
        # We still calculate unique colors just for the metadata tag, but not for logic
        uc = 0
        try:
            small = cv2.resize(cv2.imread(file_path), (100, 100), interpolation=cv2.INTER_NEAREST)
            uc = len(np.unique(small.reshape(-1, 3), axis=0))
        except: pass

        command = [
            "exiftool", "-overwrite_original",
            f"-ImageDescription={stem}: grade={grade},colors={uc}; {image_metadata}",
            file_path 
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except Exception:
            pass

    def save_image(self, img: Any, file_name: str, transformer_ids: list[str], image_metadata: str)-> None:
        truncated_filename = Path(file_name).stem
        log.info(f"--- Analysis for: {truncated_filename} ---")

        is_rejected, reason, dominance_percent, mode = self._get_analysis_verdict(img)
        
        grade = "F"
        if dominance_percent < 50.0: grade = "A"
        elif dominance_percent < 60.0: grade = "B"
        elif dominance_percent < 75.0: grade = "C"
        
        log.info(f"Mode: {mode} | Grade: {grade} | {reason}")

        current_datetime = datetime.now()
        formatted_datetime: str = current_datetime.strftime('%Y-%m-%d_%H-%M')
        transformer_ids_string = "_".join(transformer_ids)
        
        filename_parts = [grade, transformer_ids_string, formatted_datetime, common.fix_file_name(truncated_filename)]
        processed_file_name = "_".join(filename_parts) + ".jpg"

        if grade == "F":
            out_path = os.path.join(self.output_rejected_dir, processed_file_name)
            self._rejected += 1
            log.info(f"Rejected (F): {out_path}")
        else:
            out_path = os.path.join(self.output_transformed_dir, processed_file_name)
            self._accepted += 1
            log.info(f"Accepted ({grade}): {out_path}")

        cv2.imwrite(out_path, img)
        self.write_exif(out_path, truncated_filename, grade, image_metadata)

    # ... Rest of file (process_image, process_images) stays same ...
    def process_image(self, config: dict, file_path: str, transformers: list[Callable]):
        from Transformers.transformer_dictionary import transformer_ids
        random.seed(time.time())

        jpeg_path = file_path
        if ".png" in file_path.lower():
            jpeg_path = Path(file_path.replace(".png", ".jpg"))
            common.convert_png_to_jpeg(file_path, jpeg_path)

        img = cv2.imread(jpeg_path)
        if img is None: return

        transformer_id_list: list[str] = []
        self.image_metadata = ""
        
        for transformer in transformers:
            try:
                self.transformer_name = transformer.__class__.__name__
                transformer_id_list.append(self.transformer_name)
                img, _ = self.apply(config, img, transformer)[0]
            except Exception: pass

        self.save_image(img, file_path, transformer_id_list, self.image_metadata)
    
    def process_images(self, config: dict, dir: str) -> None:
        from .pipeline import get_all_transformers_dict

        source_name = Path(dir).name.lower() 
        source_config = config.get(source_name, {})
        image_type = source_config.get("image_type", "default")
        
        run_config = json.loads(json.dumps(config)) 

        pipeline_conf = run_config.get("pipeline", {})
        
        transformers_to_modify = []
        if isinstance(pipeline_conf, dict):
            transformers_to_modify = pipeline_conf.get("include", [])
        elif isinstance(pipeline_conf, list):
            transformers_to_modify = pipeline_conf
        
        for transformer_name in transformers_to_modify:
            if transformer_name not in run_config:
                run_config[transformer_name] = {}
            run_config[transformer_name]["image_type"] = image_type

        for dirpath, _, file_names in os.walk(dir):
            for file_name in file_names:
                transformers = []
                
                if isinstance(pipeline_conf, list):
                    all_transformers_map = get_all_transformers_dict() 

                    for name in pipeline_conf:
                        key = name.lower()
                        if key in all_transformers_map:
                            transformers.append(all_transformers_map[key]())
                        else:
                            log.error(f"Transformer '{name}' not found.")
                else:
                    pipeline = Pipeline(run_config.get("pipeline", None))
                    if not pipeline:
                        log.error(f"Unable to get pipeline for {dir}/{file_name}")
                        return
                    transformers = pipeline.get_transformers()

                file_path = os.path.join(dirpath, file_name)
                if os.path.isfile(file_path):
                    self.process_image(run_config, file_path, transformers)
                else:
                    log.warning(f"Skipping non-file path: {file_name}")
                    continue

    @property
    def accepted(self) -> int:
        return self._accepted

    @property
    def rejected(self) -> int:
        return self._rejected
