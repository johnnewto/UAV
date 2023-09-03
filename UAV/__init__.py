__version__ = "0.0.1"

from .logging import setup_logging, get_log_level
import os
UAV_DIR = os.path.dirname(os.path.abspath(__file__))


setup_logging(verbose=get_log_level())

from .mavlink.cam_client_server import CamClient, CamServer, test_cam_client_server
