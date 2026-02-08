import os
import sys

# Get the directory where screenArt.py lives
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import glob
from pathlib import Path
import random
import time
from . import common
from . import log

# REF_CHANGE: Import from Generators package
from .Generators import wiki, nasa, maps, goes, bubbles, lojong, bible, peripheral_drift_illusion, \
        kochSnowflake, hilbert, cubes

from .bus import ImageProcessingBus

from Libs.timeit import timeit
from collections import namedtuple
from datetime import datetime
from typing import List, Tuple

# REF_CHANGE: Renamed namedtuple
GeneratorConfig = namedtuple("GeneratorConfig", ["source", "should_erase"])

class ScreenArtMain():
    def __init__(self, config: dict):
        random.seed(time.time())
        self.config = config

        # REF_CHANGE: Renamed input_dirs -> generators
        # REF_CHANGE: ImageSource -> GeneratorConfig
        self.generators: dict[str, GeneratorConfig] = {
                "bubbles":                  
                    GeneratorConfig(source=f"{common.GENERATORS_IN}/Bubbles", should_erase=True),
                "cubes":                    
                    GeneratorConfig(source=f"{common.GENERATORS_IN}/cubes", should_erase=True),
                "nasa":                     
                    GeneratorConfig(source=f"{common.GENERATORS_IN}/Nasa", should_erase=True),
                "maps":                     
                    GeneratorConfig(source=f"{common.GENERATORS_IN}/Maps", should_erase=True),
                "goes":                     
                    GeneratorConfig(source=f"{common.GENERATORS_IN}/Goes", should_erase=True),
                "wiki":                     
                    GeneratorConfig(source=f"{common.GENERATORS_IN}/Wiki", should_erase=False),
                "lojong":                   
                    GeneratorConfig(source=f"{common.GENERATORS_IN}/Lojong", should_erase=False),
                "bible":                    
                    GeneratorConfig(source=f"{common.GENERATORS_IN}/Bible", should_erase=True),
                "peripheraldriftillusion":  
                    GeneratorConfig(source=f"{common.GENERATORS_IN}/OpticalIllusions", should_erase=True),
                "kochSnowflake":            
                    GeneratorConfig(source=f"{common.GENERATORS_IN}/KochSnowflake", should_erase=True),
                "hilbert":                  
                    GeneratorConfig(source=f"{common.GENERATORS_IN}/Hilbert", should_erase=True),
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

    @timeit # type: ignore
    def run(self):
        self.trim_images(common.TRANSFORMERS_OUT, 50)
        self.trim_images(common.REJECTED_OUT, 0)
        self.trim_images(common.WIKI_OUT, 10)

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
                nasa.Nasa(self.config).get_new_images("Nasa")
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

        menubar_path = Path(common.MENUBAR_FILE)
        log.info(menubar_path)
        menubar_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(common.MENUBAR_FILE, "w") as m:
            m.write(final_output)
            log.info(final_output)

        print(main_msg) 

def main(config: dict):
    s = ScreenArtMain(config)
    try:
        _, elapsed_time = s.run() # type: ignore
        stats = s.image_bus.get_performance_stats()
        s.write_outcome(elapsed_time, True, stats)
        exit(0)
    except Exception as e:
        log.fatal(f"An error occurred during run: {e}")
        s.write_outcome("0.0", False, [])
        exit(1)
