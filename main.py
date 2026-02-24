from .screenArt import ScreenArt
import argparse 
import os
from pathlib import Path
import sys
from multiprocessing import freeze_support 
from typing import Any, List, Tuple
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
from .Transformers.RasterTransformers import (
    AnamorphicTransformer,
    ColormapTransformer,
    DataMoshTransformer,
    DuotoneTransformer,
    FisheyeTransformer,
    FlipWilsonTransformer,
    FluidWarpTransformer,
    FractalWarpTransformer,
    GlitchWarpTransformer,
    HalftoneTransformer,
    InvertRGBTransformer,
    MeltMorphTransformer,
    NullTransformer,
    PosterizationTransformer,
    RadialWarpTransformer,
    SwirlWarpTransformer,
    ThermalImagingTransformer,
    ThreeDExtrusionTransformer,
    TritoneTransformer,
    WatercolorTransformer,
    WheelTransformer,
    XrayTransformer
)

from .Transformers.transformer_dictionary import transformer_registry
from .pipeline import ImageProcessingPipeline
from time_it import time_it # type: ignore

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
            self.log.info(f"🚨 Trimming {trim_images_count} oldest files from {directory_path}.")
            files_to_delete = sorted(image_files, key=os.path.getmtime)[:trim_images_count]

            deleted_count = 0
            for file_path in files_to_delete:
                try:
                    Path(file_path).unlink()
                    deleted_count += 1
                except OSError as e:
                    self.log.error(f"Error deleting {file_path}: {e}")
            self.log.info(f"✅ Deleted {deleted_count} files.")

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
            self.log.info(f"Running {key.capitalize()} Generator...")
            GeneratorClass().run() 
        else:
            self.log.warning(f"Generator class for key '{key}' not mapped in registry.")

    @time_it # type: ignore
    def run(self):
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

        self.log.info("----------------------------")

        return self

    def write_outcome(self, elapsed_time: str, ok: bool, stats: List[Tuple[str, float]]):
        formatted_datetime = datetime.now().strftime('%H:%M')
        mark = "✓" if ok else "❌"
        ms_value = int(float(elapsed_time))

        main_msg = f"{ms_value:02d}s@{formatted_datetime} {mark}"
        output_lines = [main_msg]

        if stats:
            for name, avg_time in stats:
                formatted_avg = f"{int(avg_time * 1000)}ms"
                clean_name = name.replace("Transformer", "")
                output_lines.append(f"{clean_name}: {formatted_avg}")
        
        output_lines.append("---")
        output_lines.append(f"{self.pipeline.accepted} accepted")
        output_lines.append(f"{self.pipeline.rejected} rejected")
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
        _, elapsed_time = s.run() # type: ignore
        stats = s.pipeline.get_performance_stats()
        s.write_outcome(elapsed_time, True, stats)
        sys.exit(0)
    except Exception as e:
        s.log.error(f"An error occurred during run: {e}")
        s.write_outcome("0.0", False, [])
        sys.exit(1)

if __name__ == "__main__":
    freeze_support() 
    run_main()
