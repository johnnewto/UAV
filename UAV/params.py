


__all__ = ['LOG_DIR', 'LOGGING_LEVEL', 'LOGGING_NAME', 'CAMERA_SOURCE', 'CAMERA_RESOLUTION', 'CAMERA_FPS', 'CAMERA_FLIP_METHOD',
           'CAMERA_FLIP', 'CAMERA_ROTATION', 'CAMERA_HFLIP', 'CAMERA_VFLIP']


_uav_home_dir = 'UAV' # subdirectory of xdg base dir
_uav_cfg_name = 'settings.toml'    # todo use https://github.com/hukkin/tomli
_uav_params_name = 'params.py'


import logging


LOG_DIR = 'logs'
LOGGING_LEVEL = logging.INFO
LOGGING_NAME = 'uav_log'



CAMERA_SOURCE = 'AIRSIM'

CAMERA_RESOLUTION = (640, 480)
CAMERA_FPS = 30
CAMERA_FLIP_METHOD = 0
CAMERA_FLIP = False
CAMERA_ROTATION = 0
CAMERA_HFLIP = False
CAMERA_VFLIP = False


