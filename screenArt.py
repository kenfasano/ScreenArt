import os
import sys

# Get the directory where screenArt.py lives
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add it to sys.path so 'Transformers' can be found
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import glob
from pathlib import Path
import random
import time
from . import common
from . import log

from .InputSources import wiki, nasa, bubbles, lojong, bible, peripheral_drift_illusion
from .bus import ImageProcessingBus
from timeit import timeit
from collections import namedtuple
from datetime import datetime
from typing import List, Tuple

ImageSource = namedtuple("ImageSource", ["source", "should_erase"])

# List of all available transformers by Class Name
ALL_RASTER_TRANSFORMERS = [
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
    "XrayTransformer"
]

class ScreenArtMain():
    def __init__(self, config: dict):
        random.seed(time.time())
        self.config = config

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
    def run(self):
        # Standard Cleanup
        self.trim_images(common.TRANSFORMERS_OUT, 50)
        self.trim_images(common.REJECTED_OUT, 0)

        # Determine inputs using the same helper logic
        keys_to_process = self._get_keys_to_process()
        
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

    def trim_images(self, directory_path: str, max_images: int):
        search_path = os.path.join(directory_path, "*.[jpP]*") 

        image_files = glob.glob(search_path)
        current_count = len(image_files)

        print(f"Current image count in '{directory_path}': {current_count}")

        if current_count >= max_images:
            trim_images_count = current_count - max_images
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

    def write_outcome(self, elapsed_time: str, ok: bool, stats: List[Tuple[str, float]]):
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime('%m/%d, %H:%M')
        mark: str = "✓" if ok else "❌"
        
        main_msg = f"{formatted_datetime} {elapsed_time} {mark}"
        
        output_lines = [main_msg]

        if stats:
            for name, avg_time in stats:
                formatted_avg = f"{avg_time:.4f}s"
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

        print(main_msg) 

def main(config: dict):
    s = ScreenArtMain(config)
    try:
        _, elapsed_time = s.run()
        
        # Retrieve stats from bus using the previous method name
        stats = s.image_bus.get_performance_stats()
        
        s.write_outcome(elapsed_time, True, stats)
        exit(0)
    except Exception as e:
        log.fatal(f"An error occurred during run: {e}")
        s.write_outcome("0.0", False, [])
        exit(1)
