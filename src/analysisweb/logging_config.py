import os
import logging

# Custom log level
VERBOSE_LEVEL_NUM = 15
logging.addLevelName(VERBOSE_LEVEL_NUM, "VERBOSE")


def get_keras_verbose(log_level):
    if log_level == logging.INFO:
        return 0
    elif log_level == logging.DEBUG:
        return 2
    else:
        return 1


def verbose(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_LEVEL_NUM):
        self._log(VERBOSE_LEVEL_NUM, message, args, **kwargs)


logging.Logger.verbose = verbose


def setup_logging():
    """Set up logging with custom VERBOSE level."""
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Handle custom level explicitly
    if log_level_str == "VERBOSE":
        log_level = VERBOSE_LEVEL_NUM
    else:
        log_level = getattr(logging, log_level_str, logging.INFO)

    # Manually configure handler to ensure custom level works
    handler = logging.StreamHandler()
    handler.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Clear and set root logger
    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()
    root.addHandler(handler)

    root.debug("Logging initialized with level: %s", log_level_str)
    
import os

