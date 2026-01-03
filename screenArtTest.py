# screenArt.py (Top-level script)
import glob
import os
import sys 
import csv 
import itertools # <--- NEW: For generating combinations
from pathlib import Path
import random
import time
from typing import Any, Optional 
from . import common
from . import log

from .InputSources import wiki, nasa, bubbles, lojong, bible, peripheral_drift_illusion
from .bus import ImageProcessingBus
from timeit import timeit
from collections import namedtuple
from datetime import datetime

ImageSource = namedtuple("ImageSource", ["source", "should_erase"])

MAX_IMAGES = 50

# List of all available transformers by Class Name
ALL_TRANSFORMERS = [
    "AnamorphicTransformer",
    "ColormapTransformer",
    "DataMoshTransformer",
    "DuotoneTransformer",
    "FisheyeTransformer",
    "FluidWarpTransformer",
    "FractalWarpTransformer",
    "GlitchWarpTransformer",
    "HalftoneTransformer",
    "InvertRGBTransformer",
    "MeltMorphTransformer",
    "NullTransformer",
    "PosterizationTransformer",
    "RadialWarpTransformer",
    "SwirlWarpTransformer",
    "ThermalImagingTransformer",
    "ThreeDExtrusionTransformer",
    "TritoneTransformer",
    "WatercolorTransformer",
    "WheelTransformer",
    "XrayTransformer"
]

class ScreenArtTestMain():
    def __init__(self, config: dict, test_csv: Optional[str] = None):
        random.seed(time.time())
        self.config = config
        self.test_csv: str | None = test_csv 

        self.input_dirs: dict[str, ImageSource] = {
                "bubbles": ImageSource(source=f"{common.INPUT_SOURCES_IN}/Bubbles", should_erase=True),
                "nasa": ImageSource(source=f"{common.INPUT_SOURCES_IN}/Nasa", should_erase=True),
                "wiki": ImageSource(source=f"{common.INPUT_SOURCES_IN}/Wiki", should_erase=True),
                "lojong": ImageSource(source=f"{common.INPUT_SOURCES_IN}/Lojong", should_erase=True),
                "bible": ImageSource(source=f"{common.INPUT_SOURCES_IN}/Bible", should_erase=True),
                "peripheraldriftillusion": ImageSource(source=f"{common.INPUT_SOURCES_IN}/OpticalIllusions", should_erase=True)
                }

        self.image_bus = ImageProcessingBus(common.TRANSFORMERS_OUT, common.REJECTED_OUT)

    def erase_image_dir(self, dir: str):
        log.info(f"Erasing directory: {dir}")
        for dirpath, _, filenames in os.walk(dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    os.remove(file_path)
                except OSError as e:
                    log.error(f"Error: {e.filename} - {e.strerror}.")

    def _get_keys_to_process(self) -> list[str]:
        """
        Helper to determine which input keys to process based on config.
        Used by both Test Mode and Normal Mode.
        """
        include_list = self.config.get("include", None)
        exclude_list = self.config.get("exclude", None)
        
        keys_to_process = []
        
        if include_list:
            for key in include_list:
                if key in self.input_dirs:
                    keys_to_process.append(key)
                else:
                    log.warning(f"Include key '{key}' maps to unknown internal source. Skipping.")
        elif exclude_list:
            all_keys = set(self.input_dirs.keys())
            excluded_keys = {key for key in exclude_list}
            keys_to_process = [key for key in all_keys if key not in excluded_keys]
        else:
            keys_to_process = list(self.input_dirs.keys())
            
        return keys_to_process

    @timeit # type: ignore
    def run(self) -> Any:
        log.info("Running...")

        # ==========================================
        # MODE 1: TEST MODE (Automatic Matrix Generation)
        # ==========================================
        if self.test_csv:
            log.info(f"***** Test mode enabled. Output will be written to {self.test_csv}")
            
            # 1. Initial Cleanup (Run ONCE at start)
            log.info("Test Mode: Initial cleanup of Transformed and Rejected directories.")
            self.erase_image_dir(common.TRANSFORMERS_OUT)
            self.erase_image_dir(common.REJECTED_OUT)

            # 2. Phase 1: Generate/Fetch Inputs (Run ONCE at start)
            keys_to_process = self._get_keys_to_process()
            log.info(f"Test Mode Input Sources: {keys_to_process}")
            
            log.info("Test Mode Phase 1: Preparing Input Sources...")
            for key in keys_to_process:
                image_source = self.input_dirs[key]
                if image_source.should_erase:
                    self.erase_image_dir(image_source.source)
                self.get_input_source(key)

            # 3. Generate Test Matrix (Cartesian Product)
            # Generates all pairs: (T1, T2)
            test_matrix = list(itertools.product(ALL_TRANSFORMERS, repeat=2))
            total_tests = len(test_matrix)
            log.info(f"Generated matrix of {total_tests} tests.")

            # 4. Open CSV for Writing
            try:
                with open(self.test_csv, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Write Header
                    writer.writerow(["Transformer1", "Transformer2", "Grade", "Ratio", "Accepted", "Rejected"])
                    
                    # 5. Loop through Generated Tests
                    for i, (t1, t2) in enumerate(test_matrix):
                        pipeline_list = [t1, t2]
                        log.info(f"--- Running Test {i+1}/{total_tests}: {pipeline_list} ---")

                        # A. Inject Transformers
                        self.config['pipeline'] = pipeline_list

                        # B. Reset Bus Statistics
                        self.image_bus._accepted = 0
                        self.image_bus._rejected = 0
                        self.image_bus.transformer_times.clear()

                        # C. Phase 2: Process Images
                        for key in keys_to_process:
                            dir_path = self.input_dirs[key].source
                            self.image_bus.process_images(self.config, dir_path)

                        # D. Calculate Stats
                        acc = self.image_bus.accepted
                        rej = self.image_bus.rejected
                        grade, ratio = common.calculate_batch_grade(acc, rej)
                        
                        log.info(f"Result: Grade={grade}, Ratio={ratio}, Acc={acc}, Rej={rej}")

                        # E. Write Result Row Immediately
                        writer.writerow([t1, t2, grade, ratio, acc, rej])
                        f.flush() # Ensure data is written to disk in case of crash

                log.info(f"Test Batch Complete. Results saved to {self.test_csv}")

            except Exception as e:
                log.fatal(f"Failed to write to test CSV: {e}")
                sys.exit(1)

            return self

        # ==========================================
        # MODE 2: NORMAL MODE
        # ==========================================
        else:
            # Standard Cleanup
            self.trim_images(common.TRANSFORMERS_OUT)

            # Determine inputs using the same helper logic
            keys_to_process = self._get_keys_to_process()
            log.info(f"Normal Mode Input Sources: {keys_to_process}")
            
            # Phase 1
            for key in keys_to_process:
                image_source = self.input_dirs[key]
                if image_source.should_erase:
                    self.erase_image_dir(image_source.source)
                self.get_input_source(key)

            # Phase 2
            for key in keys_to_process:
                dir_path = self.input_dirs[key].source
                self.image_bus.process_images(self.config, dir_path)

            return self
    
    def trim_images(self, directory_path: str):
        search_path = os.path.join(directory_path, "*.[jpP]*") 

        image_files = glob.glob(search_path)
        current_count = len(image_files)

        print(f"Current image count in '{directory_path}': {current_count}")

        if current_count >= MAX_IMAGES:
            trim_images_count = current_count - MAX_IMAGES
            print(f"🚨 Directory is full ({current_count} images). Trimming {trim_images_count} oldest files.")
            files_to_delete = sorted(image_files, key=os.path.getmtime)
            files_to_delete = files_to_delete[:trim_images_count]

            deleted_count = 0
            for file_path in files_to_delete:
                try:
                    Path(file_path).unlink()
                    deleted_count += 1
                except OSError as e:
                    print(f"    - Error deleting {file_path}: {e}")

            print(f"✅ Trim complete. Deleted {deleted_count} files.")
            print(f"New image count: {current_count - deleted_count}")

        else:
            print("Directory size is within the limit. No trimming needed.")

    def get_input_source(self, key: str):
        log.info(f"get_input_source {key=}")
        match key:
            case "wiki":
                log.info("Connecting to the Wikipedia API...")
                wiki.Wiki(self.config).get_new_images("Wiki")
            case "nasa":
                log.info("Connecting to the NASA Open Data Portal...")
                nasa.Nasa(self.config).get_new_images("Nasa")
            case "bubbles":
                log.info("Connecting to the 'Bubbles' generator...")
                bubbles.Bubbles(self.config).draw()
            case "lojong":
                log.info("Connecting to the 'Lojong' generator...")
                lojong.Lojong(self.config).draw()
            case "bible":
                log.info("Connecting to the 'Bible' generator...")
                bible.Bible(self.config).draw()
            case "peripheraldriftillusion":
                log.info("Connecting to the 'PeripheralDriftIllusion' generator...")
                peripheral_drift_illusion.PeripheralDriftIllusion(self.config).draw()
            case _:
                log.info(f"Input source for key '{key}' not found.")
                return

    def write_outcome(self, elapsed_time: str, ok: bool):
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime('%m/%d, %H:%M')
        mark: str = "✓" if ok else "❌"
        
        main_msg = f"{formatted_datetime} {elapsed_time} {mark}"
        
        output_lines = [main_msg]

        average_times = {}
        for name, times in self.image_bus.transformer_times.items():
            if times:
                avg = sum(times) / len(times)
                average_times[name] = avg

        sorted_times = sorted(average_times.items(), key=lambda item: item[1], reverse=True)

        for name, avg_time in sorted_times:
            formatted_avg = f"{avg_time:.2f} ms"
            clean_name = name.replace("Transformer", "")
            line = f"{clean_name}: {formatted_avg}"
            output_lines.append(line)
        
        accepted: int = self.image_bus.accepted
        rejected: int = self.image_bus.rejected
        output_lines.append("---")
        output_lines.append(f"{accepted} accepted")
        output_lines.append(f"{rejected} rejected")
        final_output = "\n".join(output_lines)
        
        with open(common.MENUBAR_FILE, "w") as m:
            m.write(final_output)
            log.info(final_output)

def main(config: dict, test_csv: Optional[str] = None):
    log.info("main")        
    s = ScreenArtTestMain(config, test_csv=test_csv)

    try:
        _, elapsed_time = s.run()

        s.write_outcome(elapsed_time, True)
        exit(0)
    except Exception as e:
        log.fatal(f"An error occurred during run: {e}")
        s.write_outcome("0.0", False)
        exit(1)
