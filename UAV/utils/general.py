
__all__ = [ 'boot_time', 'boot_time_str', 'get_linenumber', 'format_rcvd_msg', 'time_since_boot_ms',
           'time_UTC_usec', 'date_time_str', 'LeakyQueue', 'euler_to_quaternion', 'read_camera_dict_from_toml', 'With']

from pathlib import Path

# from fastcore.utils import *
import numpy as np # Scientific computing library for Python
import queue
import typing as typ
import time
from inspect import currentframe, getframeinfo
import toml


def get_linenumber():
    cf = currentframe()
    filename = Path(getframeinfo(cf).filename).name
    return f"{filename}:{cf.f_back.f_lineno}"


def format_rcvd_msg(msg, extra=''):
    """ Format a message for logging."""
    s = f"{str(msg)} ... {extra}"
    try:
        s = f"Rcvd {msg.get_srcSystem():3d}/{msg.get_srcComponent():3d} {s}"
    except:
        try:
            s = f"Rcvd {'???'}/{msg.get_srcComponent():3d} {s}"
        except:
            s = f"Rcvd {'???'}/{'???'} {s}"
    return s

boot_time = time.time()
boot_time_str = time.strftime("%Y-%m-%d|%H:%M:%S", time.localtime(boot_time))

def time_since_boot_ms()->int:
    """Return the time since boot in milliseconds."""
    # try:
    #     a = boot_time
    # except NameError:
    #     boot_time = time.time()
    return int((time.time() - boot_time) * 1000)

def time_UTC_usec()->int:
    return int(time.time() * 1e6)

def date_time_str()->str:
    return time.strftime("%Y-%m-%d|%H:%M:%S", time.localtime())


class LeakyQueue(queue.Queue):
    """Queue that contains only the last actual items and drops the oldest one."""

    def __init__(
        self,
        maxsize: int = 100,
        on_drop: typ.Optional[typ.Callable[["LeakyQueue", "object"], None]] = None,
    ):
        super().__init__(maxsize=maxsize)
        self._dropped = 0
        self._on_drop = on_drop or (lambda queue, item: None)

    def put(self, item, block=True, timeout=None):
        if self.full():
            dropped_item = self.get_nowait()
            self._dropped += 1
            self._on_drop(self, dropped_item)
        super().put(item, block=block, timeout=timeout)

    @property
    def dropped(self):
        return self._dropped

def read_camera_dict_from_toml(toml_file_path # path to TOML file
                               )->dict: # camera_info dict
    """Read MAVLink camera info from a TOML file."""
    camera_dict = toml.load(toml_file_path)
    return camera_dict

# def read_camera_info_from_toml(toml_file_path):
#     """Read MAVLink camera info from a TOML file."""
#     with open(toml_file_path, 'rb') as file:
#         data = toml.load(file)
#
#     camera_info = data['camera_info']
#     camera_info['vendor_name'] = [int(b) for b in camera_info['vendor_name'].encode()]
#     camera_info['model_name'] = [int(b) for b in camera_info['model_name'].encode()]
#     # Extract camera_info
#     return data['camera_info']


def euler_to_quaternion(roll:float, # roll (rotation around x-axis)  angle in radians 
                        pitch:float, #  attitude (rotation around y-axis) angle in radians
                        yaw:float, # direction (rotation around z-axis) angle in radians
                        ) -> list: # orientation in quaternion [x,y,z,w] format
  """
  Convert an Euler angle to a quaternion.
"""   
  qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
  qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
  qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
  qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
 
  return [qx, qy, qz, qw]


class With(object):
    """Break out of the with statement"""
    class Break(Exception):
      """Break out of the with statement"""

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value.__enter__()

    def __exit__(self, etype, value, traceback):
        error = self.value.__exit__(etype, value, traceback)
        if etype == self.Break:
            return True
        return error