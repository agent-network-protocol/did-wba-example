import logging
import logging.handlers
import os
import sys
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        levelname = record.levelname
        message = super().format(record)
        color = self.COLORS.get(levelname, self.COLORS["RESET"])
        return color + message + self.COLORS["RESET"]


def setup_logging(level=logging.INFO):
    # Get project name
    project_name = os.path.basename(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ).replace("-", "_")

    # Create log directory
    if sys.platform == "darwin":  # Mac system
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
        )
    else:
        log_dir = f"/var/log/{project_name}"
    try:
        # If directory doesn't exist, create it and set permissions
        if not os.path.exists(log_dir):
            os.system("sudo mkdir -p " + log_dir)
            os.system(
                f"sudo chown -R {os.getenv('USER')} " + log_dir
            )
        os.makedirs(log_dir, exist_ok=True)
    except Exception as e:
        print(f"Error setting up log directory: {e}")
        # If failed, use backup log directory
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
        )
        os.makedirs(log_dir, exist_ok=True)

    # Generate log filename (including date)
    log_file = os.path.join(
        log_dir, f"{project_name}_{datetime.now().strftime('%Y%m%d')}.log"
    )

    print("Log file: ", log_file)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Configure colored console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    colored_formatter = ColoredFormatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s\n"
    )
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)

    # Configure file handler with the same format (but without colors)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    # Prevent log messages from propagating to the root logger
    logger.propagate = False

    return logger


# To maintain backward compatibility, keep set_log_color_level function, but make it call setup_logging
def set_log_color_level(level):
    return setup_logging(level)
