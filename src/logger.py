import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s :: %(levelname)s :: %(message)s")

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # ou logging.INFO
console_handler.setFormatter(formatter)

log_file = "app.log"
file_handler = RotatingFileHandler("app.log", maxBytes=1_000_000, backupCount=5)
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

