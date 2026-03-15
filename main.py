from .Transformers.RasterTransformers.rasterTransformer import RasterTransformer
from .screenArt import ScreenArt
import argparse 
import os
from pathlib import Path
import sys
from multiprocessing import freeze_support 
import glob
import random
import time
from datetime import datetime
from tqdm import tqdm

# 1. Import your Generators
from .Generators import (
    bible,
    bubbles,
    cubes,
    goes,
    lojong,
    maps,
    nasa,
    peripheral_drift_illusion,
    wiki 
)

# 2. Explicitly Import your Raster Transformers for the Pipeline

from .Transformers.transformer_dictionary import transformer_registry
from .pipeline import ImageProcessingPipeline

class ScreenArtMain(ScreenArt):
    def __init__(self):
        super().__init__("ScreenArt")
        random.seed(time.time())

        gen_in = self.config["paths"]["generators_in"]

        # 1. GENERATOR DIRECTORIES
        self.generators: dict[str, str] = {
            "bubbles":                f"{gen_in}/bubbles",
            "cubes":                  f"{gen_in}/cubes",
            "nasa":                   f"{gen_in}/nasa",
            "maps":                   f"{gen_in}/maps",
            "goes":                   f"{gen_in}/goes",
            "wiki":                   f"{gen_in}/wiki",
            "lojong":                 f"{gen_in}/lojong",
            "bible":                  f"{gen_in}/bible",
            "peripheraldriftillusion":f"{gen_in}/opticalillusions",
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
            # kochSnowflake and hilbert excluded — linear generators, not raster
        }

        # Pull requested transformers from screenArt.conf, default to colormap
        requested_transformers = self.config.get("transformers", ["colormap"])
        self.active_transformers = []
        
        for t_key in requested_transformers:
            TransformerClass: RasterTransformer = transformer_registry.get(t_key.lower().replace("transformer",""))
            if TransformerClass:
                self.active_transformers.append(TransformerClass())
            else:
                self.log.warning(f"Transformer '{t_key}' not found in registry. Skipping.")

        # Initialize the pipeline
        self.pipeline = ImageProcessingPipeline()
        self.generator_stats: dict[str, float] = {}

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
            with self.timer() as t:
                generator = GeneratorClass()
                generator.run() 
            self.generator_stats[generator.__class__.__name__] = t.elapsed
        else:
            self.log.warning(f"Generator class for key '{key}' not mapped in registry.")

    def run(self) -> str:
        elapsed = None
        with self.timer("Total", "s") as t:
            self.trim_images(self.config["paths"]["transformers_out"], 50)
            self.trim_images(self.config["paths"]["rejected_out"], 50)
            self.trim_images(self.config["paths"]["wiki_out"], 10)

            keys_to_process = self._get_keys_to_process()
            
            # Phase 1: Run Generators

            self.generator_stats: dict[str, float] = {}
            for key in (bar := tqdm(keys_to_process, desc="Generators  ", unit="gen", ncols=80)):
                self.erase_image_dir(self.generators[key])
                self.run_generator(key)

            # Phase 2: Run Transformers
            for key in (bar := tqdm(keys_to_process, desc="Transformers", unit="tra", ncols=80)):
                self.pipeline.run(self.generators[key], transformers=self.active_transformers)

        elapsed = str(t.elapsed)
        self.log.debug("----------------------------")
        return elapsed

    def format_stats(self, stats: dict[str, list[float] | float], strip_word: str = "") -> list[str]:
        formatted_lines = []
        
        if not stats:
            return formatted_lines

        list_stats: dict[str, list[float]] = {k: v for k, v in stats.items() if isinstance(v, list)}
        float_stats: dict[str, float] = {k: v for k, v in stats.items() if isinstance(v, (int, float))}

        if list_stats:
            sorted_stats = sorted(
                list_stats.items(),
                key=lambda item: sum(item[1]) / len(item[1]) if item[1] else 0,
                reverse=True
            )
        else:
            sorted_stats = sorted(
                float_stats.items(),
                key=lambda item: item[1],
                reverse=True
            )

        for name, times in sorted_stats:
            if not times:
                continue
            
            if list_stats:
                min_time = round(min(times)) #type: ignore
                max_time = round(max(times)) #type: ignore
                avg_time = round(sum(times) / len(times))  #type: ignore
                self.log.info(name)
                formatted_times = (
                    f"{name:32s} -> "
                    f"Min: {min_time:5d}ms | "
                    f"Avg: {avg_time:5d}ms | "
                    f"Max: {max_time:5d}ms"
                )
            else:
                formatted_times = (
                    f"{name:26s} -> "
                    f"{round(times):5d}ms" #type: ignore     
                )

            formatted_lines.append(formatted_times)

        return formatted_lines

    def write_outcome(self, elapsed_time: str, ok: bool, accepted_rejected: str, pipeline_stats: dict[str, list[float]] | None):
        formatted_datetime = datetime.now().strftime('%H:%M')
        mark = "✓" if ok else "❌"
        ms_value = int(float(elapsed_time))

        main_msg = f"{ms_value:02d}s@{formatted_datetime} {mark}\n{accepted_rejected}"
        output_lines = [main_msg]
        output_lines.append("---") # Optional separator between sections

        # 1. Process and append the Generator Stats
        if self.generator_stats:
            # Use extend() to add the returned list of strings to our main output
            output_lines.extend(self.format_stats(self.generator_stats, strip_word="Generator"))
            output_lines.append("---") # Optional separator between sections

        # 2. Process and append the Pipeline Stats
        if pipeline_stats:
            # Process the pipeline transformer stats
            output_lines.extend(self.format_stats(pipeline_stats, strip_word="Transformer")) #type: ignore
      
        final_output = "\n".join(output_lines)
        
        results_file = os.path.join(self.config["paths"]["results_file_dir"], "results.txt")
        with open(results_file, "w") as m:
            m.write(final_output)
            
        self.log.info(final_output)

        # --- Split display: panel 1 (summary + generators), then panel 2 (transformers) ---
        # Locate the two "---" separators; split after the second one
        sep_indices = [i for i, line in enumerate(output_lines) if line == "---"]

        if len(sep_indices) >= 2:
            split_index = sep_indices[1] + 1  # include the second "---"
            panel1_lines = output_lines[:split_index]
            panel2_lines = output_lines[split_index:]
        else:
            panel1_lines = output_lines
            panel2_lines = []

        os.system("clear")
        print("\n".join(panel1_lines))

        if panel2_lines:
            time.sleep(12)
            os.system("clear")
            print("\n".join(panel2_lines))

    def run_files(self, file_paths: list[str], count: int = 1) -> str:
        """
        Transform a list of explicit file paths, bypassing all generators.
        Each file is transformed `count` times with independently sampled
        transformer sets, producing up to len(file_paths) * count outputs.
        """
        import shutil, tempfile

        # Validate and resolve paths
        valid = []
        for p in file_paths:
            resolved = Path(p).expanduser().resolve()
            if resolved.is_file() and resolved.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                valid.append(resolved)
            else:
                self.log.warning(f"Skipping '{p}': not a valid image file.")

        if not valid:
            self.log.error("No valid image files provided to -f/--files.")
            return "0"

        with self.timer("Total", "s") as t:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Copy each file into the temp dir `count` times with unique names
                for src in valid:
                    for i in range(count):
                        self.log.info(f"{src} #{i}")
                        stem = src.stem if count == 1 else f"{src.stem}_{i+1}"
                        dst = Path(tmp_dir) / f"{stem}{src.suffix}"
                        shutil.copy2(src, dst)

                self.log.info(f"run_files: {len(valid)} file(s) × {count} = {len(valid)*count} inputs → {tmp_dir}")
                self.pipeline.run(tmp_dir, transformers=self.active_transformers)

        return str(t.elapsed)

def run_main():
    parser = argparse.ArgumentParser(description="Run the image processing and transformation pipeline.")
    parser.add_argument('-c', '--config', type=str, help='Override the transformation file specified in the config.')
    parser.add_argument('-t', '--test', type=str, help='Path to a CSV file for test mode.')
    parser.add_argument('-f', '--files', type=str, nargs='+', help='One or more image file paths to transform directly, bypassing generators.')
    parser.add_argument('-n', '--count', type=int, default=1, help='Number of transformed outputs to produce per input file (default: 1).')
    args, _ = parser.parse_known_args()

    s = ScreenArtMain()
    try:
        if args.files:
            elapsed = s.run_files(args.files, args.count) or ""
        else:
            elapsed = s.run() or ""
        accepted_rejected = s.pipeline.get_accepted_rejected()
        pipeline_stats = s.pipeline.get_performance_stats()
        s.write_outcome(elapsed, True, accepted_rejected, pipeline_stats)
        sys.exit(0)
    except Exception as e:
        s.log.error(f"An error occurred during run: {e}")
        s.write_outcome("0.0", False, "", None)
        sys.exit(1)

if __name__ == "__main__":
    freeze_support() 
    run_main()
