# logger_config.py
import logging
import sys

'''
Levels:
    DEBUG: Detailed internal data (arrays, values)
    INFO: Normal lifecycle events (connected, started)
    WARNING: Recoverable issues (device not found, errors caught)
    ERROR: Serious failures that affect functionality
    CRITICAL: Application cannot continue

'''
def configure_logging(level=logging.DEBUG):
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),          # console
            logging.FileHandler("testtoolsuite.log"),   # file
        ]
    )
