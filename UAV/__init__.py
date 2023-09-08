__version__ = "0.0.2"
import time, os, sys
# Set the environment variable before from pymavlink import mavutil  library is imported
os.environ['MAVLINK20'] = '1'
from .logging import setup_logging, get_log_level
import os
UAV_DIR = os.path.dirname(os.path.abspath(__file__))


setup_logging(verbose=get_log_level())

from .mavlink.mavcom import MAVCom, mavutil, MAV_TYPE_GCS, MAV_TYPE_CAMERA
from .mavlink.component import Component