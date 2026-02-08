import logging
import os
import sys

LOG_FILE = "ScreenArt/screenArt.log"

# --- MOVED SETUP INTO THIS FUNCTION ---
def setup_logging():
    """Configures the logging system. This should only be called ONCE."""
    
    print("configuring the logging system...") # This will now run only once

    # All your original basicConfig, moved here
    logging.basicConfig(
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w'),  # 'w' overwrites each time
            logging.StreamHandler()
        ],

        format='%(levelname)s: %(message)s',
        level=logging.INFO
    )
    
    # Get the main logger and log that setup is done
    log = logging.getLogger()
    log.info("Logging configured successfully.")
# --- END OF NEW FUNCTION ---


def caller() -> tuple:
    frame = sys._getframe(2)  # 2 = skip wrapper + logging fn
    caller_file = os.path.basename(frame.f_code.co_filename)
    caller_function = frame.f_code.co_name
    caller_line = frame.f_lineno
    caller_class = None
    if 'self' in frame.f_locals:
        caller_class = type(frame.f_locals['self']).__name__
    return caller_file, caller_class, caller_function, caller_line

def debug(message: str):     
    file, cls, func, line = caller()
    prefix = f"[{file}:{line}]"
    if cls:
        prefix += f" [{cls}.{func}]"
    else:
        prefix += f" [{func}]"
    logging.log(logging.DEBUG, f"{prefix} {message}")

def info(message: str):     
    file, cls, func, line = caller()
    prefix = f"[{file}:{line}]"
    if cls:
        prefix += f" [{cls}.{func}]"
    else:
        prefix += f" [{func}]"
    logging.log(logging.INFO, f"{prefix} {message}")

def warning(message: str):  
    file, cls, func, line = caller()
    prefix = f"[{file}:{line}]"
    if cls:
        prefix += f" [{cls}.{func}]"
    else:
        prefix += f" [{func}]"
    logging.log(logging.WARNING, f"{prefix} {message}")

def error(message: str) -> bool:    
    file, cls, func, line = caller()
    prefix = f"[{file}:{line}]"
    if cls:
        prefix += f" [{cls}.{func}]"
    else:
        prefix += f" [{func}]"
    logging.log(logging.ERROR, f"{prefix} {message}")
    return False

def critical(message: str): 
    file, cls, func, line = caller()
    prefix = f"[{file}:{line}]"
    if cls:
        prefix += f" [{cls}.{func}]"
    else:
        prefix += f" [{func}]"
    logging.log(logging.CRITICAL, f"{prefix} {message}")

def fatal(message: str):    
    file, cls, func, line = caller()
    prefix = f"[{file}:{line}]"
    if cls:
        prefix += f" [{cls}.{func}]"
    else:
        prefix += f" [{func}]"
    logging.log(logging.FATAL, f"{prefix} {message}")
