from .Transformers.RasterTransformers.rasterTransformer import RasterTransformer
from .screenArt import ScreenArt
import argparse
import os
from pathlib import Path
import sys
from multiprocessing import freeze_support
import glob
import humanize
import random
import shutil
import subprocess
import logging
import time
from datetime import datetime
from tqdm import tqdm

LOGGER = logging.getLogger(__name__)

# 1. Import your Generators
from .Generators import (
    asciiScreenArt,
    bible,
    bubbles,
    cubes,
    goes,
    lojong,
    mandala_draw,
    maps,
    nasa,
    numinous,
    peripheral_drift_illusion,
    staticFavorites,
    staticMandala,
    wiki
)

# 1. GENERATOR REGISTRY (Map the string key directly to the Class)
GENERATOR_REGISTRY = {
    "ascii_screen_art": asciiScreenArt.AsciiScreenArt,
#    "bible": bible.Bible,
    "bubbles": bubbles.Bubbles,
    "cubes": cubes.Cubes,
    "goes": goes.GoesGenerator,
#    "lojong": lojong.Lojong,
    "mandala_draw": mandala_draw.MandalaDraw,
    "maps": maps.NasaMapGenerator,
    "nasa": nasa.Nasa,
    "numinous": numinous.Numinous,
    "peripheraldriftillusion": peripheral_drift_illusion.PeripheralDriftIllusion,
#    "static_favorites": staticFavorites.StaticFavorites,
    "static_mandala": staticMandala.StaticMandala,
    "wiki": wiki.Wiki,
    # kochSnowflake and hilbert excluded — linear generators, not raster
}

# Explicitly Import your Raster Transformers for the Pipeline

from .Transformers.transformer_dictionary import transformer_registry
from .pipeline import ImageProcessingPipeline

class ScreenArtMain(ScreenArt):
    def __init__(self):
        super().__init__("ScreenArt")
        random.seed(time.time())
        self.log = getattr(self, "log", LOGGER)

        self.generators, self.generator_classes = self._build_generators()

        # Pull requested transformers from screenArt.conf, default to colormap
        requested_transformers = self.config.get("transformers", ["colormap"])
        self.active_transformers = []
        
        for t_key in requested_transformers:
            TransformerClass: RasterTransformer | None = transformer_registry.get(t_key.lower().replace("transformer",""))
            if TransformerClass:
                self.active_transformers.append(TransformerClass())
            else:
                self.log.warning(f"Transformer '{t_key}' not found in registry. Skipping.")

        # Initialize the pipeline
        self.pipeline = ImageProcessingPipeline()
        self.generator_stats: dict[str, float] = {}

    # A method that builds both dicts, skipping missing config entries
    def _build_generators(self) -> tuple[dict[str, str], dict[str, type]]:
        paths: dict[str, str] = {}
        classes: dict[str, type] = {}

        for name, cls in GENERATOR_REGISTRY.items():
            config_key = f"{name}_out"
            if config_key in self.config["paths"]:
                path = self.config["paths"][config_key]
                classes[name] = cls
                # check that the subdirectory exists
                if os.path.isdir(os.path.expanduser(path)):
                    paths[name] = path
                    classes[name] = cls
                else:
                    self.log.warning(f"{path} not found")
            else:
                self.log.warning(f"key {config_key} not found in conf")

        return paths, classes

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

        self.log.info(f"trim_images: {search_path=}, {current_count=}")
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
            self.log.info(f"✅ Deleted {deleted_count} files.")

    def _get_keys_to_process(self) -> list[str]:
        include_list = self.config.get("include", None)
        exclude_list = self.config.get("exclude", None)

        if isinstance(include_list, list):
            return [k for k in include_list if k in self.generators]
        elif isinstance(exclude_list, list):
            excluded_keys = set(exclude_list)
            return [k for k in self.generators.keys() if k not in excluded_keys]

        return list(self.generators.keys())

    def run_generator(self, key: str) -> None:
        """Instantiate and run one registered generator."""
        generator_class = self.generator_classes.get(key)
        output_dir = self.generators.get(key)

        if generator_class is None or output_dir is None:
            raise KeyError(f"Generator '{key}' is not configured.")

        self.log.info("Starting generator '%s' -> %s", key, output_dir)
        started = time.perf_counter()

        try:
            generator = generator_class(output_dir)
            generator.run()
        except Exception:
            self.log.exception("Generator '%s' failed after %.3fs", key,
                               time.perf_counter() - started)
            raise

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        self.generator_stats[generator.__class__.__name__] = elapsed_ms
        self.log.info("Completed generator '%s' in %.1f ms", key, elapsed_ms)

    def run(self) -> int:
        """Run all configured generators and then the transformer pipeline.

        Returns elapsed time in milliseconds. Exceptions are logged with a
        traceback and then re-raised so the process exits non-zero.
        """
        started = time.perf_counter()
        self.generator_stats = {}

        try:
            transformer_out = self.config["paths"]["transformers_out"]
            wiki_out = self.config["paths"]["wiki_out"]

            self.trim_images(transformer_out, 25)
            self.trim_images(wiki_out, 10)

            keys_to_process = self._get_keys_to_process()
            if not keys_to_process:
                self.log.warning("No generators selected; nothing to process.")
                return 0

            self.log.info("Selected generators: %s", ", ".join(keys_to_process))

            # Phase 1: generators
            for key in tqdm(
                keys_to_process,
                desc="Generators  ",
                unit="gen",
                ncols=80,
            ):
                output_dir = self.generators[key]
                self.log.debug("Clearing generator output directory: %s", output_dir)
                self.erase_image_dir(output_dir)
                self.run_generator(key)

            # Phase 2: transformers
            for key in tqdm(
                keys_to_process,
                desc="Transformers",
                unit="tra",
                ncols=80,
            ):
                output_dir = self.generators[key]
                self.log.info("Starting transformers for '%s'", key)
                try:
                    self.pipeline.run(
                        output_dir,
                        transformers=self.active_transformers,
                    )
                except Exception:
                    self.log.exception(
                        "Transformer pipeline failed for generator '%s'", key
                    )
                    raise
                self.log.info("Completed transformers for '%s'", key)

            elapsed_ms = (time.perf_counter() - started) * 1000.0
            self.log.info("Complete run finished in %.1f ms", elapsed_ms)
            return int(elapsed_ms)

        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            self.log.exception("ScreenArt run failed after %.1f ms", elapsed_ms)
            raise

    def format_generator_stats(self, stats: dict[str, list[float] | float], strip_word: str = "") -> list[str]:
        formatted_lines = []
        
        if not stats:
            return formatted_lines

        float_stats: dict[str, float] = {k: v for k, v in stats.items() if isinstance(v, (int, float))}

        sorted_stats = sorted(
            float_stats.items(),
            key=lambda item: item[1],
            reverse=True
        )

        for name, times in sorted_stats:
            if not times:
                continue
            
            name = name.strip()
            # Calculate the value first
            single_time = humanize.intcomma(round(times, 0))                      #type: ignore
            single_time_str = f"{single_time:>12}ms"
            
            # Then format it with alignment
            formatted_times = f"{name:<25} {single_time_str}"

            formatted_lines.append(formatted_times)

        return formatted_lines

    def prepare_pipeline_stats(self, data: dict[str, list[int]]) -> dict[str, int]:
        summed_data = {k: sum(v) for k, v in data.items()}
        top_four = dict(sorted(summed_data.items(), key=lambda item: item[1], reverse=True)[:4])
        return top_four

    def write_outcome(self, elapsed_time: int, ok: bool, accepted_rejected: str, pipeline_stats: dict[str, list[float]] | None):
        formatted_datetime = datetime.now().strftime('%H:%M')
        mark = "✓" if ok else "❌"

        self.log.info(f"{elapsed_time=}")
        main_msg = f"{elapsed_time:,}ms@{formatted_datetime} {mark}\t{accepted_rejected}"
        output_lines = [main_msg]

        transformed_dir = Path(self.config["paths"]["transformers_out"])
        try:
            files = [f for f in transformed_dir.rglob("*") if f.is_file()]
            dir_bytes = sum(f.stat().st_size for f in files)
            file_count = len(files)
        except OSError:
            self.log.exception("Unable to calculate output directory statistics: %s", transformed_dir)
            dir_bytes = 0
            file_count = 0
        
        if dir_bytes >= 1 << 30:
            dir_size_str = f"{dir_bytes / (1 << 30):.2f} GB"
        elif dir_bytes >= 1 << 20:
            dir_size_str = f"{dir_bytes / (1 << 20):.2f} MB"
        else:
            dir_size_str = f"{dir_bytes / (1 << 10):.2f} KB"
            output_lines.append(f"Images: {dir_size_str} ({file_count})") 
            
        output_lines.append("") # Optional separator between sections

        # 1. Process and append the Generator Stats
        if self.generator_stats:
            # Use extend() to add the returned list of strings to our main output
            output_lines.extend(self.format_generator_stats(self.generator_stats, strip_word="Generator")) #type: ignore
            output_lines.append("") # Optional separator between sections

        # 2. Process and append the Pipeline Stats
        # {'RadialWarpTransformer': [24, 20, 19, 20, 23, 11], '
        if pipeline_stats:
            stats = self.prepare_pipeline_stats(pipeline_stats)
            stats_list = []
            for key, value in stats.items():
                stats_list.append(f"{key:<25} {humanize.intcomma(value):>12}ms")

            output_lines.extend(stats_list)

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

    def run_files(self, file_paths: list[str], count: int = 1) -> int:
        """Transform explicit image files, bypassing all generators.

        Returns elapsed time in milliseconds. Invalid input is treated as an
        error and raises ValueError so the top-level entry point can return a
        non-zero exit status.
        """
        if count < 1:
            raise ValueError(f"count must be >= 1, got {count}")

        started = time.perf_counter()
        self.log.info("run_files: %d file(s), count=%d", len(file_paths), count)

        valid: list[Path] = []
        for raw_path in file_paths:
            path = Path(raw_path).expanduser().resolve()
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                valid.append(path)
                self.log.debug("Accepted image: %s", path)
            else:
                self.log.warning("Skipping invalid image file: %s", raw_path)

        if not valid:
            raise ValueError("No valid image files provided to -f/--files.")

        try:
            import tempfile

            with tempfile.TemporaryDirectory(prefix="screenart-") as tmp_dir:
                tmp_path = Path(tmp_dir)

                for src in valid:
                    for index in range(count):
                        stem = src.stem if count == 1 else f"{src.stem}_{index + 1}"
                        dst = tmp_path / f"{stem}{src.suffix}"
                        shutil.copy2(src, dst)

                total_inputs = len(valid) * count
                self.log.info(
                    "Prepared %d input(s) in temporary directory %s",
                    total_inputs,
                    tmp_path,
                )

                try:
                    self.pipeline.run(
                        tmp_path,
                        transformers=self.active_transformers,
                    )
                except Exception:
                    self.log.exception("Transformer pipeline failed for explicit files")
                    raise

        except OSError:
            self.log.exception("File operation failed while processing explicit files")
            raise

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        self.log.info("run_files completed in %.1f ms", elapsed_ms)
        return int(elapsed_ms)

    def run_dirs(self, dir_paths: list[str], count: int = 1) -> int:
        """Transform up to five randomly selected entries from each directory."""
        if count < 1:
            raise ValueError(f"count must be >= 1, got {count}")

        started = time.perf_counter()
        self.log.info("run_dirs: %d director(y/ies), count=%d", len(dir_paths), count)

        total_elapsed_ms = 0
        for raw_dir in dir_paths:
            directory = Path(raw_dir).expanduser().resolve()

            if not directory.is_dir():
                raise NotADirectoryError(f"Not a directory: {directory}")

            # Only select regular image files. This avoids accidentally passing
            # subdirectories or unrelated files to run_files().
            image_files = [
                path for path in directory.iterdir()
                if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
            ]
            selected = random.sample(image_files, min(5, len(image_files)))

            self.log.info(
                "Directory %s: %d image(s), selected %d",
                directory,
                len(image_files),
                len(selected),
            )

            for file_path in selected:
                total_elapsed_ms += self.run_files([str(file_path)], count)

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        self.log.info(
            "run_dirs completed in %.1f ms (sum of pipeline times: %d ms)",
            elapsed_ms,
            total_elapsed_ms,
        )
        return int(elapsed_ms)

def run_main() -> int:
    """Parse command-line arguments, run ScreenArt, and return an exit code."""
    parser = argparse.ArgumentParser(
        description="Run the image processing and transformation pipeline."
    )
    parser.add_argument(
        "-c", "--config", type=str,
        help="Override the transformation file specified in the config.",
    )
    parser.add_argument(
        "-t", "--test", type=str,
        help="Path to a CSV file for test mode.",
    )
    parser.add_argument(
        "-d", "--dirs", type=str, nargs="+",
        help="One or more image directory paths to transform directly, bypassing generators.",
    )
    parser.add_argument(
        "-f", "--files", type=str, nargs="+",
        help="One or more image file paths to transform directly, bypassing generators.",
    )
    parser.add_argument(
        "-n", "--count", type=int, default=1,
        help="Number of transformed outputs to produce per input file (default: 1).",
    )

    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be >= 1")

    try:
        screen_art = ScreenArtMain()

        if args.files:
            screen_art.log.info("Mode: explicit files")
            elapsed = screen_art.run_files(args.files, args.count)
        elif args.dirs:
            screen_art.log.info("Mode: directories")
            elapsed = screen_art.run_dirs(args.dirs, args.count)
        else:
            screen_art.log.info("Mode: generators")
            elapsed = screen_art.run()

        accepted_rejected = screen_art.pipeline.get_accepted_rejected()
        pipeline_stats = screen_art.pipeline.get_performance_stats()
        screen_art.write_outcome(
            elapsed,
            True,
            accepted_rejected,
            pipeline_stats,
        )

        screen_art.log.info("ScreenArt completed successfully.")
        return 0

    except KeyboardInterrupt:
        LOGGER.warning("Interrupted by user.")
        return 130

    except Exception:
        LOGGER.exception("ScreenArt terminated with an unhandled exception.")

        # write_outcome is useful for the UI/results file, but must not hide
        # the original failure if reporting itself fails.
        try:
            if "screen_art" in locals():
                screen_art.write_outcome(0, False, "", None)
        except Exception:
            LOGGER.exception("Failed to write the failure outcome.")

        return 1


if __name__ == "__main__":
    freeze_support()
    sys.exit(run_main())
