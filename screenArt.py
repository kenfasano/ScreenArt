import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Any, Optional
import time
from contextlib import contextmanager

class ScreenArt(ABC):
    # Class-level singleton storage for the configuration
    _global_config: Optional[dict[str, Any]] = None

    def __init__(self, project_name="ScreenArt"):
        self.project_name = project_name
        self.os_type = sys.platform  # 'darwin' for Mac, 'linux' for Fedora
        
        # Base project path (e.g., /home/kenfasano/Scripts/ScreenArt or /Users/kenfasano/Scripts/ScreenArt)
        self.base_path = os.path.expanduser(f"~/Scripts/{self.project_name}")

        # 1. Load Config FIRST (Singleton pattern)
        if ScreenArt._global_config is None:
            ScreenArt._global_config = self._setup_config()
        self.config: dict[str, Any] = ScreenArt._global_config

        # 2. Expand and ensure all paths from the config exist
        self._expand_and_ensure_paths()

        # 3. Setup Logging
        self._setup_logging()

    def _setup_logging(self):
        """Configures standard logging to both file and console."""
        # Pull log directory from the config, or fallback to a default logs folder
        self.log_path = self.config.get("paths", {}).get("log_path", os.path.join(self.base_path, "logs"))
        self.log_file = os.path.join(self.log_path, "screenArt.log")

        # Ensure the directory exists before creating the handler
        os.makedirs(self.log_path, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.log = logging.getLogger(self.project_name)
        self.log.debug(f"ScreenArt superclass initialized on {self.os_type}. Paths expanded.")

    def _setup_config(self) -> dict[str, Any]:
        """Finds and loads the config file, checking sys.argv for overrides."""
        config_path = os.path.join(self.base_path, "screenArt.conf")

        # Check sys.argv for '-c' or '--config' without requiring argparse here
        for i, arg in enumerate(sys.argv):
            if arg in ['-c', '--config'] and i + 1 < len(sys.argv):
                config_path = sys.argv[i + 1]
                break

        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            # Print instead of log, because the logger isn't ready yet at this stage
            print(f"CRITICAL: Could not load config at {config_path}: {e}")
            sys.exit(1)

    def _expand_and_ensure_paths(self):
        """Pulls paths from the config, expands tildes, handles OS quirks, and creates directories."""
        raw_paths = self.config.get("paths", {})
        is_darwin = self.os_type == "darwin"

        for key, path_str in raw_paths.items():
            # Handle the macOS Google Drive pathing requirement
            if is_darwin and "Google Drive" in path_str and "My Drive" not in path_str:
                path_str = path_str.replace("Google Drive", "Google Drive/My Drive")

            # Expand the tilde to the absolute user directory
            folder = Path(path_str).expanduser()
            
            try:
                folder.mkdir(parents=True, exist_ok=True)
                os.chmod(folder, 0o755) 
                raw_paths[key] = str(folder)
            except PermissionError:
                print(f"CRITICAL: System denied permission to create {folder}")
            except Exception as e:
                print(f"ERROR: Could not create directory {folder}: {e}")

        # Update the config dictionary with the fully resolved absolute paths
        self.config["paths"] = raw_paths

    def get_output_filename(self, extension="png"):
        """Generates a timestamped filename for generic art output."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.config.get("paths", {}).get("output", os.path.join(self.base_path, "output"))
        return os.path.join(output_dir, f"art_{timestamp}.{extension}")

    def check_os_config(self):
        """Helper to return specific commands based on current environment."""
        if self.os_type == "linux":
            return {"wallpaper_cmd": "swww", "shell": "zsh"}
        elif self.os_type == "darwin":
            return {"wallpaper_cmd": "osascript", "shell": "zsh"}
        return {"wallpaper_cmd": None, "shell": "sh"}

    @contextmanager
    def timer(self, custom_name=None, unit="ms"):
        """Context manager to time a block of code and log the duration."""
        start_time = time.perf_counter()
        
        try:
            yield 
        finally:
            end_time = time.perf_counter()
            elapsed_seconds = end_time - start_time
            
            log_name = custom_name or self.__class__.__name__
            
            # Format based on the requested unit
            if unit == "s":
                self.log.info(f"{log_name}: {elapsed_seconds:.2f}s")
            else:
                elapsed_ms = elapsed_seconds * 1000
                self.log.info(f"{log_name}: {elapsed_ms:.2f}ms")

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """
        Each ScreenArt agent MUST implement its own execution logic.
        *args and **kwargs allow Generators (0 args) and Transformers (1+ args) 
        to share this exact same contract.
        """
        pass
