# run.py
import argparse 
import json
import os
from pathlib import Path
import sys
from .log import setup_logging
from . import screenArt
from multiprocessing import freeze_support 

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
    config_filepath = args.config or "ScreenArt/default.sa"
    config = {}
    try:
        with open(config_filepath, 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load or parse config file {config_filepath}. Using defaults. Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get the directory of the current script
    current_dir = Path(__file__).resolve().parent
    sys.path.append(str(current_dir))

    screenArt.main(config)

if __name__ == '__main__':
    freeze_support() 
    setup_logging()
    run_processing()
