from .screenArt import ScreenArt
import argparse 
import os
from pathlib import Path
import sys
from multiprocessing import freeze_support 
from typing import List, Tuple
import glob
import random
import time
from collections import namedtuple
from datetime import datetime

# 1. Import your Generators
from .Generators import (
    bible,
    bubbles,
    cubes,
    goes,
    hilbert,
    kochSnowflake,
    lojong,
    maps,
    nasa,
    peripheral_drift_illusion,
    wiki 
)

# 2. Explicitly Import your Raster Transformers for the Pipeline

from .Transformers.transformer_dictionary import transformer_registry
from .pipeline import ImageProcessingPipeline

GeneratorConfig = namedtuple("GeneratorConfig", ["source", "should_erase"])

class ScreenArtMain(ScreenArt):
    def __init__(self):
        super().__init__("ScreenArt")
        random.seed(time.time())

        gen_in = self.config["paths"]["generators_in"]
        
        # 1. GENERATOR CONFIGURATIONS (Where do they output, and should we erase?)
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

        # 2. GENERATOR REGISTRY (Map the string key directly to the Class)
        self.generator_classes = {
            "wiki": wiki.Wiki,
            "nasa": nasa.Nasa,
            "maps": maps.NasaMapGenerator,
            "goes": goes.GoesGenerator,
            "bubbles": bubbles.Bubbles,
            "cubes": cubes.Cubes,
            "lojong": lojong.Lojong,
            "bible": bible.Bible,
            "peripheraldriftillusion": peripheral_drift_illusion.PeripheralDriftIllusion,
            "kochSnowflake": kochSnowflake.KochSnowflake,
            "hilbert": hilbert.Hilbert,
        }

        # Pull requested transformers from screenArt.conf, default to colormap
        requested_transformers = self.config.get("transformers", ["colormap"])
        self.active_transformers = []
        
        for t_key in requested_transformers:
            TransformerClass = transformer_registry.get(t_key.lower().replace("transformer",""))
            if TransformerClass:
                self.active_transformers.append(TransformerClass())
            else:
                self.log.warning(f"Transformer '{t_key}' not found in registry. Skipping.")

        # Initialize the pipeline
        self.pipeline = ImageProcessingPipeline()

    def erase_image_dir(self, directory: str):
        for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    os.remove(file_path)
                except OSError as e:
                    self.log.error(f"Error deleting {file_path}: {e.strerror}")

    def trim_images(self, directory_path: str, max_images: int):
        search_path = os.path.join(directory_path, "*.[jpP]*") 
        image_files = glob.glob(search_path)
        current_count = len(image_files)

        if current_count >= max_images and max_images > 0:
            trim_images_count = current_count - max_images
            self.log.debug(f"🚨 Trimming {trim_images_count} oldest files from {directory_path}.")
            files_to_delete = sorted(image_files, key=os.path.getmtime)[:trim_images_count]

            deleted_count = 0
            for file_path in files_to_delete:
                try:
                    Path(file_path).unlink()
                    deleted_count += 1
                except OSError as e:
                    self.log.error(f"Error deleting {file_path}: {e}")
            self.log.debug(f"✅ Deleted {deleted_count} files.")

    def _get_keys_to_process(self) -> list[str]:
        include_list = self.config.get("include", None)
        exclude_list = self.config.get("exclude", None)
        
        if include_list:
            return [k for k in include_list if k in self.generators]
        elif exclude_list:
            excluded_keys = set(exclude_list)
            return [k for k in self.generators.keys() if k not in excluded_keys]
        
        return list(self.generators.keys())

    def run_generator(self, key: str):
        """Dynamically instantiates and runs a generator from the registry."""
        GeneratorClass = self.generator_classes.get(key)
        if GeneratorClass:
            self.log.debug(f"Running {key.capitalize()} Generator...")
            GeneratorClass().run() 
        else:
            self.log.warning(f"Generator class for key '{key}' not mapped in registry.")

    def run(self) -> str:
        elapsed = None
        with self.timer("Total", "s") as t:
            self.trim_images(self.config["paths"]["transformers_out"], 50)
            self.trim_images(self.config["paths"]["rejected_out"], 0)
            self.trim_images(self.config["paths"]["wiki_out"], 10)

            keys_to_process = self._get_keys_to_process()
            
            # Phase 1: Run Generators
            for key in keys_to_process:
                gen_config = self.generators[key]
                if gen_config.should_erase:
                    self.erase_image_dir(gen_config.source)
                self.run_generator(key)

            # Phase 2: Run Transformers
            for key in keys_to_process:
                dir_path = self.generators[key].source
                # Choose a random number between 1 and 4 (but no more than the total available  )
                num_to_pick = random.randint(1, min(4, len(self.active_transformers)))
        
                # Select unique transformers
                transformers_to_apply = random.sample(self.active_transformers, num_to_pick)
                self.pipeline.run(dir_path, transformers=transformers_to_apply)

        elapsed = str(t.elapsed)
        self.log.debug("----------------------------")
        return elapsed

    def write_outcome(self, elapsed_time: str, ok: bool, stats: dict[str, list[int]]):
        formatted_datetime = datetime.now().strftime('%H:%M')
        mark = "✓" if ok else "❌"
        ms_value = int(float(elapsed_time))

        main_msg = f"{ms_value:02d}s@{formatted_datetime} {mark}"
        output_lines = [main_msg]

        if stats:
            sorted_stats = sorted(
                stats.items(), 
                key=lambda item: sum(item[1]) / len(item[1]) if item[1] else 0, 
                reverse=True
            )
            output_lines.append(f"{self.pipeline.accepted} accepted")
            output_lines.append(f"{self.pipeline.rejected} rejected")
            output_lines.append("---")

            for name, times in sorted_stats:
                # Prevent division by zero if a list somehow ends up empty
                if not times:
                    continue
                
                # Calculate the metrics
                min_time = round(min(times))
                max_time = round(max(times))
                avg_time = round(sum(times) / len(times))
                
                # Format the numbers (e.g., rounded to 2 decimal places)
                formatted_stats = (
                    f"Min: {min_time:4d}ms | "
                    f"Avg: {avg_time:4d}ms | "
                    f"Max: {max_time:4d}ms"
                )
                
                # Clean up the name and append to output
                clean_name = name.replace("Transformer", "")
                output_lines.append(f"{clean_name:16s}: {formatted_stats}")        

        output_lines.append("===")
        final_output = "\n".join(output_lines)
        
        results_file = os.path.join(self.config["paths"]["results_file_dir"], "results.txt")
        with open(results_file, "w") as m:
            m.write(final_output)
            
        self.log.info(final_output)

def run_main():
    parser = argparse.ArgumentParser(description="Run the image processing and transformation pipeline.")
    parser.add_argument('-c', '--config', type=str, help='Override the transformation file specified in the config.')
    parser.add_argument('-t', '--test', type=str, help='Path to a CSV file for test mode.')
    args, _ = parser.parse_known_args()

    s = ScreenArtMain()
    try:
        elapsed = s.run() or ""
        stats = s.pipeline.get_performance_stats()
        s.write_outcome(elapsed, True, stats)
        sys.exit(0)
    except Exception as e:
        s.log.error(f"An error occurred during run: {e}")
        s.write_outcome("0.0", False, [])
        sys.exit(1)

if __name__ == "__main__":
    freeze_support() 
    run_main()
