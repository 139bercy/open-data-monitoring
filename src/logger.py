import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s :: %(levelname)s :: %(message)s")

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # ou logging.INFO
console_handler.setFormatter(formatter)

import os

if not logger.hasHandlers():
    logger.addHandler(console_handler)
    
    if os.getenv("OPEN_DATA_MONITORING_ENV") != "TEST":
        file_handler = RotatingFileHandler("app.log", maxBytes=1_000_000, backupCount=5)
        file_handler.setLevel(logging.WARN)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
