import argparse 
import json
import os
from pathlib import Path
import sys
from multiprocessing import freeze_support 
from typing import Any # Import Any for flexible dicts
import glob
import random
import time
from . import log

CONFIG="ScreenArt/screenArt.conf"

from .Generators import wiki, nasa, maps, goes, bubbles, lojong, bible, peripheral_drift_illusion, \
        kochSnowflake, hilbert, cubes

from .bus import ImageProcessingBus

from time_it import time_it # type: ignore
from collections import namedtuple
from datetime import datetime
from typing import List, Tuple

# REF_CHANGE: Renamed namedtuple
GeneratorConfig = namedtuple("GeneratorConfig", ["source", "should_erase"])

class ScreenArtMain():
    def __init__(self, config: dict[str, Any]):
        random.seed(time.time())
        self.config = config
        self.get_expanded_paths()

        gen_in = self.paths["generators_in"]
        self.generators: dict[str, GeneratorConfig] = {
                "bubbles": GeneratorConfig(source=f"{gen_in}/bubbles", should_erase=True),
                "cubes": GeneratorConfig(source=f"{gen_in}/cubes", should_erase=True),
                "nasa": GeneratorConfig(source=f"{gen_in}/nasa", should_erase=True),
                "maps": GeneratorConfig(source=f"{gen_in}/maps", should_erase=True),
                "goes": GeneratorConfig(source=f"{gen_in}/goes", should_erase=True),
               "wiki": GeneratorConfig(source=f"{gen_in}/wiki", should_erase=False),
                "lojong": GeneratorConfig(source=f"{gen_in}/lojong", should_erase=False),
                "bible": GeneratorConfig(source=f"{gen_in}/bible", should_erase=True),
                "peripheraldriftillusion": GeneratorConfig(source=f"{gen_in}/opticalillusions", should_erase=True),
                "kochSnowflake": GeneratorConfig(source=f"{gen_in}/kochsnowflake", should_erase=True),
                "hilbert": GeneratorConfig(source=f"{gen_in}/hilbert", should_erase=True),
                }

        self.image_bus = ImageProcessingBus(self.paths["transformers_out"], self.paths["rejected_out"])

    def get_expanded_paths(self):
        raw_paths = self.config.get("paths", {})
        is_darwin = sys.platform == "darwin" # Check if we are on macOS

        for key, path_str in raw_paths.items():
            # 1. Handle the macOS "My Drive" requirement
            if is_darwin and "Google Drive" in path_str and "My Drive" not in path_str:
                path_str = path_str.replace("Google Drive", "Google Drive/My Drive")

            # 2. Expand the tilde (~) to /Users/kenfasano or /home/ken
            folder = Path(path_str).expanduser()
            
            try:
                folder.mkdir(parents=True, exist_ok=True)
                os.chmod(folder, 0o755) 
                raw_paths[key] = str(folder)
                log.debug("SUCCESS: {folder} is ready for writing.")
            except PermissionError:
                log.critical(f"CRITICAL: System denied permission to create {folder}")
            except Exception as e:
                log.critical(f"ERROR: {e}")

        self.paths = self.config["paths"] = raw_paths
        
    def erase_image_dir(self, dir: str):
        for dirpath, _, filenames in os.walk(dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    os.remove(file_path)
                except OSError as e:
                    log.error(f"Error: {e.filename} - {e.strerror}.")

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
        else:
            print("Directory size is within the limit. No trimming needed.")

    def _get_keys_to_process(self) -> list[str]:
        include_list = self.config.get("include", None)
        exclude_list = self.config.get("exclude", None)
        
        keys_to_process = []
        
        if include_list:
            for key in include_list:
                if key in self.generators:
                    keys_to_process.append(key)
                else:
                    log.warning(f"Include key '{key}' maps to unknown generator. Skipping.")
        elif exclude_list:
            all_keys = set(self.generators.keys())
            excluded_keys = {key for key in exclude_list}
            keys_to_process = [key for key in all_keys if key not in excluded_keys]
        else:
            keys_to_process = list(self.generators.keys())
            
        return keys_to_process

    @time_it # type: ignore
    def run(self):
        self.trim_images(self.paths["transformers_out"], 50)
        self.trim_images(self.paths["rejected_out"], 0)
        self.trim_images(self.paths["wiki_out"], 10)

        keys_to_process = self._get_keys_to_process()
        
        # Phase 1: Run Generators
        for key in keys_to_process:
            gen_config = self.generators[key]
            if gen_config.should_erase:
                self.erase_image_dir(gen_config.source)
            self.run_generator(key)

        # Phase 2: Process Images
        for key in keys_to_process:
            dir_path = self.generators[key].source
            self.image_bus.process_images(self.config, dir_path)

        return self

    # REF_CHANGE: Renamed method get_input_source -> run_generator
    def run_generator(self, key: str):
        match key:
            case "wiki":
                log.info("Running Wikipedia Generator...")
                wiki.Wiki(self.config).draw()
            case "nasa":
                log.info("Running NASA Generator...")
                nasa.Nasa(self.config).get_new_images("nasa")
            case "maps":
                log.info("Running NASA Maps Generator...")
                maps.NasaMapGenerator(self.config).draw()
            case "goes":
                log.info("Running NASA GOES Generator...")
                goes.GoesGenerator(self.config).draw()
            case "bubbles":
                log.info("Running Bubbles Generator...")
                bubbles.Bubbles(self.config).draw()
            case "cubes":
                log.info("Running Cubes Generator...")
                cubes.Cubes(self.config).draw()
            case "lojong":
                log.info("Running Lojong Generator...")
                lojong.Lojong(self.config).draw()
            case "bible":
                log.info("Running Bible Generator...")
                bible.Bible(self.config).draw()
            case "peripheraldriftillusion":
                log.info("Running PeripheralDrift Generator...")
                peripheral_drift_illusion.PeripheralDriftIllusion(self.config).draw()
            case "kochSnowflake":
                log.info("Running KochSnowflake Generator...")
                kochSnowflake.KochSnowflake(self.config).draw()
            case "hilbert":
                log.info("Running Hilbert Generator...")
                hilbert.Hilbert(self.config).draw()
            case _:
                log.info(f"Generator for key '{key}' not found.")
                return

    def write_outcome(self, elapsed_time: str, ok: bool, stats: List[Tuple[str, float]]):
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime('%H:%M')
        mark: str = "✓" if ok else "❌"
        ms_value = int(float(elapsed_time))

        main_msg = f"{ms_value:02d}s@{formatted_datetime} {mark}"
        log.info(main_msg)
        
        output_lines = [main_msg]

        if stats:
            for name, avg_time in stats:
                formatted_avg = f"{int(avg_time * 1000)}ms"
                clean_name = name.replace("Transformer", "")
                line = f"{clean_name}: {formatted_avg}"
                output_lines.append(line)
        
        accepted: int = self.image_bus.accepted
        rejected: int = self.image_bus.rejected
        output_lines.append("---")
        output_lines.append(f"{accepted} accepted")
        output_lines.append(f"{rejected} rejected")
        final_output = "\n".join(output_lines)
        
        with open(self.paths["results_file_dir"] + "/results.txt", "w") as m:
            m.write(final_output)
            log.info(final_output)

        print(main_msg) 

def run_processing():
    # 1. Set up argparse
    parser = argparse.ArgumentParser(description="Run the image processing and transformation pipeline.")
    
    # CHANGED: Swapped -t to -c (config) to free up -t for test
    parser.add_argument('-c', '--config', type=str,
                        help='Override the transformation file specified in the config.')
    
    # NEW: Added -t for test csv
    parser.add_argument('-t', '--test', type=str,
                        help='Path to a CSV file for test mode (format: trans1,trans2,grade).')

    # Use parse_known_args() to avoid crashing on unrecognized arguments
    args, _ = parser.parse_known_args()

    # 2. Determine the config file path (command line overrides default)
    # CHANGED: references args.config instead of args.transformation
    config_filepath = args.config or CONFIG
    print(f"{config_filepath=}")
    config = {}
    try:
        with open(config_filepath, 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load or parse config file {config_filepath}. Using defaults. Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get the directory where screenArt.py lives
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"{current_dir}")
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    s = ScreenArtMain(config)
    try:
        _, elapsed_time = s.run() # type: ignore
        stats = s.image_bus.get_performance_stats()
        s.write_outcome(elapsed_time, True, stats)
        exit(0)
    except Exception as e:
        print(f"An error occurred during run: {e}")
        log.fatal(f"An error occurred during run: {e}")
        s.write_outcome("0.0", False, [])
        exit(1)

if __name__ == "__main__":
    freeze_support() 
    log.setup_logging()  # Changed from setup_logging()
    run_processing()
