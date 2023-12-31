# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/api/15_airsim.client.ipynb.

# %% auto 0
__all__ = ['logger']

# %% ../../nbs/api/15_airsim.client.ipynb 5
from UAV.airsim_python_client import MultirotorClient
import UAV.params as params
from UAV.utils import config_dir
import logging
from UAV.airsim.client import AirSimClient

# %% ../../nbs/api/15_airsim.client.ipynb 6
logging.basicConfig(format='%(asctime)-8s,%(msecs)-3d %(levelname)5s [%(filename)10s:%(lineno)3d] %(message)s',
                    datefmt='%H:%M:%S',
                    level=params.LOGGING_LEVEL)
logger = logging.getLogger(params.LOGGING_NAME)
