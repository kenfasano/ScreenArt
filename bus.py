import os
import random
import subprocess
import time
from . import common
from . import log

from pathlib import Path
from time_it import time_it
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

from .pipeline import Pipeline, get_transformer_dicts

# --- Constants for Analysis ---
NUM_CORES: int = 4
NUM_HUE_BUCKETS: int = 36 
NUM_LUMA_BUCKETS: int = 20
SAT_THRESH_CV2: float = 0.03 * 255
VAL_THRESH_CV2: float = 0.05 * 255
REJECTION_THRESHOLD_PERCENT: float = 75.0

# --- BUBBLES ALLOW-LIST ---
ALLOWED_BUBBLE_TRANSFORMERS = [
    "radialwarptransformer",
    "meltmorphtransformer",
    "fractalwarptransformer",
    "wheelTransformer",
    "meltmorphtransformer",
    "radialwarptransformer",
    "threedextrusiontransformer",
    "watercolortransformer",
]

# swirlwarptransformer creates vertical and horizontal roads out of any image - fix!
# radialwarp OK
# fractalwarp not doing much

ALLOWED_LINEAR_TRANSFORMERS = [
    "colormaptransformer",
    "fisheyetransformer",
    "flipwilsontransformer"
]

# REF_CHANGE: Renamed Constant
PASS_THROUGH_GENERATORS = [
    "cubes",
    "kochsnowflake",
    "hilbert",
    "wiki"
]

LINEAR_FILENAME_SUBSTRINGS = []

# --- REJECTION BYPASS LIST ---
PASS_THROUGH_TRANSFORMERS = [
    "WheelTransformer",
    "FlipWilsonTransformer"
]
# --------------------------

def _process_chunk(rgb_chunk: np.ndarray, num_buckets: int) -> np.ndarray:
    try:
        hsv_chunk: np.ndarray = rgb2hsv(rgb_chunk)
        hue: np.ndarray = hsv_chunk[..., 0]        
        saturation: np.ndarray = hsv_chunk[..., 1] 
        value: np.ndarray = hsv_chunk[..., 2]      

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

    @time_it #type: ignore 
    def apply(self, config: dict, img: Any, transformer: Any):
        processed_img = img.copy()
        try:
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
            self.transformer_times[t_name].append(end_ts - start_ts)

        except Exception as e:
            log.error(f"Error in {transformer.__class__.__name__}: {e}")      
        return processed_img, self

    def get_performance_stats(self) -> List[Tuple[str, float]]:
        if not self.transformer_times:
            return []
        stats = []
        for name, times in self.transformer_times.items():
            if times:
                avg_time = sum(times) / len(times)
                stats.append((name, avg_time))
        stats.sort(key=lambda x: x[1], reverse=True)
        return stats

    def analyze_image_hues_from_data(self, img_np_bgr: np.ndarray) -> Optional[np.ndarray]:
        try:
            img_np_rgb = cv2.cvtColor(img_np_bgr, cv2.COLOR_BGR2RGB)
            image_data: np.ndarray = img_np_rgb.astype(np.float32) / 255.0
            if image_data.size == 0:
                return None
            chunks: List[np.ndarray] = np.array_split(image_data, NUM_CORES, axis=0)
            worker_func = partial(_process_chunk, num_buckets=NUM_HUE_BUCKETS)
            with Pool(processes=NUM_CORES) as pool:
                results = pool.map(worker_func, chunks)
            total_histogram: np.ndarray = np.sum(results, axis=0)
            return total_histogram
        except Exception as e:
            log.error(f"Error during hue analysis: {e}")
            return None

    def analyze_image_luminance(self, img_np_bgr: np.ndarray) -> Optional[np.ndarray]:
        try:
            gray = cv2.cvtColor(img_np_bgr, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [NUM_LUMA_BUCKETS], [0, 256])
            return hist.flatten().astype(np.int64)
        except Exception as e:
            log.error(f"Error during luminance analysis: {e}")
            return None

    def check_is_grayscale(self, img_np_bgr: np.ndarray) -> bool:
        try:
            small = cv2.resize(img_np_bgr, (100, 100), interpolation=cv2.INTER_NEAREST)
            hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
            s = hsv[:,:,1]
            v = hsv[:,:,2]
            colored_pixels_mask = (s > SAT_THRESH_CV2) & (v > VAL_THRESH_CV2)
            colored_count = np.count_nonzero(colored_pixels_mask)
            total_count = small.shape[0] * small.shape[1]
            percent_colored = colored_count / total_count
            return percent_colored < 0.01
        except Exception:
            return False

    def _get_analysis_verdict(self, img_np_bgr: np.ndarray) -> Tuple[bool, str, float, str]:
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
        
        if not is_grayscale_mode:
            max_adjacent_sum = 0.0
            for i in range(NUM_HUE_BUCKETS):
                next_i = (i + 1) % NUM_HUE_BUCKETS 
                adjacent_sum = percentages[i] + percentages[next_i]
                if adjacent_sum > max_adjacent_sum:
                    max_adjacent_sum = adjacent_sum
            dominance_value = max(dominance_value, float(max_adjacent_sum))

        reason = f"{dominance_value:.1f}% max dominance in {mode_label}."
        
        _ = dominance_value > REJECTION_THRESHOLD_PERCENT

        return _, reason, dominance_value, mode_label

    def write_exif(self, file_path: str, stem: str, grade: str, image_metadata: str):
        uc = 0
        try:
            small = cv2.resize(cv2.imread(file_path), (100, 100), interpolation=cv2.INTER_NEAREST)
            uc = len(np.unique(small.reshape(-1, 3), axis=0))
        except: 
            pass

        command = [
            "exiftool", "-overwrite_original",
            f"-ImageDescription={stem}: grade={grade},colors={uc}; {image_metadata}",
            file_path 
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except Exception: pass

    def save_image(self, img: Any, file_name: str, transformer_ids: list[str], image_metadata: str)-> None:
        truncated_filename = Path(file_name).stem

        # Initialize defaults
        pass_through_generator = False
        grade = "F"

        # 1. Check Generator Bypass
        # REF_CHANGE: Using PASS_THROUGH_GENERATORS
        for generator in PASS_THROUGH_GENERATORS:
            if generator in file_name:
                grade = "P"
                pass_through_generator = True
                mode = "PassThrough"
                reason = f"Pass-through allowed by generator '{generator}'"
                break

        # 2. If not bypass, run standard analysis
        if not pass_through_generator:
            _, reason, dominance_percent, mode = self._get_analysis_verdict(img)
            
            grade = "F"
            if dominance_percent < 50.0:
                grade = "A"
            elif dominance_percent < 60.0:
                grade = "B"
            elif dominance_percent < 75.0: 
                grade = "C"
        
            # --- Check for Pass-Through Transformers ---
            active_ids_lower = [t.lower() for t in transformer_ids]
            
            for pt_name in PASS_THROUGH_TRANSFORMERS:
                pt_short = pt_name.replace("Transformer", "").lower()
                
                if pt_short in active_ids_lower:
                    if "wheel" in pt_short:
                        try:
                            small = cv2.resize(img, (100, 100), interpolation=cv2.INTER_NEAREST)
                            uc = len(np.unique(small.reshape(-1, 3), axis=0))
                            
                            if uc > 2:
                                grade = "P"
                                reason = f"Pass-through allowed by {pt_name} ({uc} colors)"
                            else:
                                grade = "F"
                                reason = f"Rejected by {pt_name} ({uc} colors <= 2)"
                        except Exception as e:
                            log.warning(f"Color check failed for {pt_name}: {e}")
                    else:
                        grade = "P"
                        reason = f"Pass-through allowed by {pt_name}"
                    break

        # 3. Finalize and Save
        current_datetime = datetime.now()
        formatted_datetime: str = current_datetime.strftime('%Y-%m-%d_%H-%M')
        transformer_ids_string = "_".join(transformer_ids)
        
        filename_parts = [grade, transformer_ids_string, formatted_datetime, common.fix_file_name(truncated_filename)]
        processed_file_name = "_".join(filename_parts) + ".jpg"

        if grade == "F":
            out_path = os.path.join(self.output_rejected_dir, processed_file_name)
            self._rejected += 1
        else:
            out_path = os.path.join(self.output_transformed_dir, processed_file_name)
            self._accepted += 1

        cv2.imwrite(out_path, img)
        self.write_exif(out_path, truncated_filename, grade, image_metadata)

    def process_image(self, config: dict, file_path: str, transformers: list[Callable]):
        random.seed(time.time())

        jpeg_path = file_path
        if ".png" in file_path.lower():
            jpeg_path = Path(file_path.replace(".png", ".jpg"))
            common.convert_png_to_jpeg(file_path, jpeg_path)

        img = cv2.imread(jpeg_path)
        if img is None: 
            return

        transformer_name_list: list[str] = []
        self.image_metadata = ""
        
        for transformer in transformers:
            try:
                self.transformer_name = transformer.__class__.__name__.replace("Transformer", "")
                transformer_name_list.append(self.transformer_name)
                img, _ = self.apply(config, img, transformer)[0] #type: ignore 
            except Exception: 
                pass

        self.save_image(img, file_path, transformer_name_list, self.image_metadata)

    def _get_transformers_from_allowlist(self, allow_list: List[str]) -> List[Any]:
        transformers = []
        raster_dict, linear_dict = get_transformer_dicts()
        all_transformers_map = {**raster_dict, **linear_dict}
        
        for name in allow_list:
            key = name.lower()
            if key in all_transformers_map:
                transformers.append(all_transformers_map[key]())
            else:
                log.warning(f"Allow-List Transformer '{name}' not found.")
        return transformers
    
    def process_images(self, config: dict, dir: str) -> None:
        is_bubbles = "bubbles" in dir
        is_cubes = "cubes" in dir
        is_koch_snowflake = "koch" in dir
        is_hilbert = "hilbert" in dir

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
                restricted_allow_list = None
                
                if is_bubbles:
                    restricted_allow_list = ALLOWED_BUBBLE_TRANSFORMERS
                elif is_koch_snowflake or is_hilbert:
                    restricted_allow_list = ALLOWED_LINEAR_TRANSFORMERS
               # elif is_space:
               #     restricted_allow_list = ALLOWED_PHOTO_TRANSFORMERS
                
                if restricted_allow_list is not None:
                    if restricted_allow_list:
                        transformers_objs = self._get_transformers_from_allowlist(restricted_allow_list)
                        if transformers_objs:
                            transformers = [random.choice(transformers_objs)]
                    else:
                        transformers = []
                else:
                    if isinstance(pipeline_conf, list):
                        raster_dict, linear_dict = get_transformer_dicts()
                        all_transformers_map = {**raster_dict, **linear_dict}
                        
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
                        
                        raster_transformers, linear_transformers = pipeline.get_transformers()
                        
                        use_linear = any(sub in file_name for sub in LINEAR_FILENAME_SUBSTRINGS)
                        
                        if use_linear:
                            transformers = linear_transformers
                        else:
                            transformers = raster_transformers

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
