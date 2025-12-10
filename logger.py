import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if missing
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, "hms.log")

# Configure root logger
logger = logging.getLogger("hms")
logger.setLevel(logging.INFO)

# File handler (rotating)
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5              # Keep last 5 logs
)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Log format
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%H:%M:%S"
)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers only once
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
