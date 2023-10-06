import os
import logging
from colorlog import ColoredFormatter
import typing as typ
from enum import Enum

LOG_BASE_NAME = 'uav'
# LOG_FORMAT = '%(levelname)-6.6s | %(name)-20s | %(asctime)s.%(msecs)03d | %(threadName)s | %(message)s'
# LOG_DATE_FORMAT = '%d.%m %H:%M:%S'
# LOG_FORMAT = '%(asctime)-8s,%(msecs)-3d %(levelname)5s [%(filename)10s:%(lineno)3d] %(message)s'
LOG_FORMAT = '%(log_color)s%(levelname)-6.6s | %(name)-15.15s | %(asctime)s.%(msecs)03d | %(filename)10s:%(lineno)3d | %(threadName)-18.18s | %(message)s'
# LOG_DATE_FORMAT = '%H:%M:%S'
LOG_DATE_FORMAT = '%S'


class NamedEnum(Enum):
    def __repr__(self):
        return str(self)

    @classmethod
    def names(cls) -> typ.List[str]:
        return list(cls.__members__.keys())

class LogLevels():
    """Log Levels from logging"""
    NONE = logging.NOTSET
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    CRITICAL = logging.CRITICAL
    TRACE = logging.DEBUG - 1

def get_log_level():
    return int(os.getenv("UAV_LOG_LEVEL", logging.DEBUG / 10)) * 10


def setup_logging(verbose: int = logging.DEBUG):
    """Configure console logging. Info and below go to stdout, others go to stderr. """

    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.DEBUG if verbose > 0 else logging.INFO)

    log_handler = logging.StreamHandler()
    log_handler.setFormatter(ColoredFormatter(
        fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT))

    local_logger = logging.getLogger(LOG_BASE_NAME)
    local_logger.setLevel(verbose)

    if not root_logger.handlers:   # don't add handlers if they already exist
        root_logger.addHandler(log_handler)

logging.getLogger('matplotlib').setLevel(logging.WARNING) # disable matplotlib font manager debug messages