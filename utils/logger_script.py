
import logging
import urllib3

class ColoredFormatter(logging.Formatter):
    """
    Special custom formatter for colorizing log messages!
    """

    # ANSI colours
    BLACK = '\033[0;30m'
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    BROWN = '\033[0;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    GREY = '\033[0;37m'

    DARK_GREY = '\033[1;30m'
    LIGHT_RED = '\033[1;31m'
    LIGHT_GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    LIGHT_BLUE = '\033[1;34m'
    LIGHT_PURPLE = '\033[1;35m'
    LIGHT_CYAN = '\033[1;36m'
    WHITE = '\033[1;37m'

    RESET = "\033[0m"

    def __init__(self, *args, **kwargs):
        self._colors = {
            logging.DEBUG: self.DARK_GREY,
            logging.INFO: self.RESET,
            logging.WARNING: self.BROWN,
            logging.ERROR: self.RED,
            logging.CRITICAL: self.LIGHT_RED,
            logging.exception: self.LIGHT_RED
            }
        super(ColoredFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        """Applies the color formats to the log level name"""
        # Save original levelname
        original_levelname = record.levelname
        original_msg = record.msg

        # Colorize the levelname
        if record.levelno in self._colors:
            colored_levelname = self._colors[record.levelno] + original_levelname + self.RESET
            record.levelname = colored_levelname
            colored_msg = self._colors[record.levelno] + original_msg + self.RESET
            record.msg = colored_msg

        # Proceed with the standard formatting
        formatted_message = logging.Formatter.format(self, record)

        # Revert to avoid affecting other loggers
        record.levelname = original_levelname
        record.msg = original_msg

        return formatted_message

    def setLevelColor(self, logging_level, escaped_ansi_code):
        self._colors[logging_level] = escaped_ansi_code

@staticmethod
def instantiate_logger() -> logging.Logger:
    """
    Create a beautiful coloured logger
    
    :returns: logger - logging.Logger instance
    """
    try:
        # Create logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        # Create a handler
        console_handler = logging.StreamHandler()

        # Set the ColoredFormatter to the handler
        formatter = ColoredFormatter("%(asctime)s | %(levelname)s | %(filename)s: %(funcName)s | %(message)s")
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(console_handler)

        return logger
    except Exception as error:
        print(f"Error in instantiating logger: {error}")
        return None

logger = instantiate_logger()
