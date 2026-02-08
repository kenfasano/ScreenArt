# run.py
import argparse 
import json
import os
import sys
from . import log
from .log import setup_logging
from . import screenArtTest
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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    sys.path.append(project_root)

    # CHANGED: Pass the test_csv argument to main for test
    #screenArtTest.main(config, test_csv=args.test)
    screenArtTest.main(config, test_csv=args.test)

if __name__ == '__main__':
    freeze_support() 
    setup_logging()
    log.info("freeze_support() and setup_logging() called; calling run_processing.") 
    run_processing()
