__all__ = ['ViewsheenGimbal']

import time
import socket

import numpy as np

from .gimbal import Gimbal
from ..logging import LogLevels
from ..utils import config_dir

from ..airsim.client import AirSimClient
import threading
# from ..camera_sdks.viewsheen.gimbal_cntrl import pan_tilt, snapshot, zoom, VS_IP_ADDRESS, VS_PORT

# Define the IP address and port number of the viewsheengimbal
VS_IP_ADDRESS = '192.168.144.200'
VS_PORT = 2000


# cams = ["high_res", "front_center", "front_right", "front_left", "bottom_center", "back_center"]
# quaternion reotate 90 degrees around z axis

# def rotate_camera_pitch_yaw(self, camera_name,
#                             pitch,
#                             yaw,
#                             ):
#     pose = super(AirSimClient, self).simGetCameraInfo(camera_name).pose
#     existing_orientation = pose.orientation
#     # get the vector of the existing orientation
#     existing_angles = airsim.to_eularian_angles(existing_orientation)
#     print(f"{existing_angles = }")
#

class ViewsheenGimbal(Gimbal):
    """ adjust the orientation of the gimbal"""

    def __init__(self,
                 camera_name="center",  # todo change this
                 settings_dict=None,  # settings dict
                 loglevel=LogLevels.INFO):  # log flag
        self.camera_name = camera_name
        self.settings_dict = settings_dict

        # _dict = settings_dict['gstreamer_video_src']
        self._dont_wait = threading.Event()  # used to pause or resume the thread

        config_file = config_dir() / "viewsheen_gimbal.toml"  # todo put this in toml file
        _VS_IP_ADDRESS = '192.168.144.200'  # todo put this in toml file
        _VS_PORT = 2000  # todo put this in toml file

        self._dont_wait = threading.Event()  # used to pause or resume the thread
        super().__init__(loglevel=loglevel)
        self.log.info(f"***** ViewsheenGimbal: {camera_name = } ******")
        self.connect()

    def connect(self, timeout=2):
        """Connect to the viewsheen_sdk gimbal"""
        # # todo,  ping it first to see if gimbal present
        # self.log.error(f" Ping it first before , Connecting to gimbal, doesn't time out if not present")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)  # Set a timeout
        try:
            self.sock.connect((VS_IP_ADDRESS, VS_PORT))
        except socket.timeout:
            self.log.error(f"Timeout connecting to gimbal")
            return False
        self.log.debug(f"Connected to gimbal")
        return True

    def rotate_cam(self, pitch, yaw):
        """Rotate the camera"""
        self.log.info(f"Rotating camera by {pitch = } {yaw = }")
        self.camera_angle[0] += pitch
        self.camera_angle[2] += yaw
        # Convert angles to radians
        pitch = np.deg2rad(self.camera_angle[0])
        yaw = np.deg2rad(self.camera_angle[2])
        self.asc.set_camera_orientation(camera_name=self.camera_name, roll=0, pitch=pitch, yaw=yaw)

    def _set_pitch_yaw(self, pitch, yaw, pitchspeed, yawspeed):
        """Set the attitude of the gimbal"""   # todo this is only the relative tilting and panning
        pan = int(yawspeed * 100)
        tilt = int(pitchspeed * 100)
        data = set_pan_tilt(pan, tilt)
        print(f"pan tilt {pan = } {tilt = } {data = }")
        self.sock.sendall(data)

    def set_pitch_yaw(self, pitch, yaw, pitchspeed, yawspeed):
        """Set the attitude of the gimbal"""
        self.log.error(f"set_pitch_yaw is not implmented for viewsheen")


    def set_yaw(self, yaw):
        """Set the attitude of the gimbal"""   # todo fix tilting and panning
        # pan = int(yawspeed * 100)
        data = set_yaw(yaw)

        print(f"{yaw = } {data = }")
        self.sock.sendall(data)

    def set_pitch(self, pitch):
        data = set_pitch(pitch)
        print(f" {pitch = } {data = }")
        self.sock.sendall(data)

    def close(self):
        """Close the gimbal."""
        self.log.info("Closing  AirsimGimbal")


# Viewsheen hardware
# IP_ADDRESS = "10.5.0.2"  # send to drone from the GS
# PORT = 2000

wCRC_Table = [
    0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
    0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400
]
def crc_fly16(pBuffer, length):
    crcTmp = 0xFFFF
    for i in range(length):
        tmp = wCRC_Table[(pBuffer[i] ^ crcTmp) & 15] ^ (crcTmp >> 4)
        crcTmp = wCRC_Table[((pBuffer[i] >> 4) ^ tmp) & 15] ^ (tmp >> 4)
    return crcTmp


def int16_to_bytes(value):
    # Extract the low and high bytes
    low_byte = value & 0xFF
    high_byte = (value >> 8) & 0xFF
    # Return the bytes as a bytearray
    return bytearray([low_byte, high_byte])

def set_pan_tilt(pan=0.0, tilt=0.0):
    ''' pan and or tilt in deg / sec with max of 100 deg / sec'''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x04
    lower_bound , upper_bound = -10000, 10000
    pan = max(lower_bound, min(int(pan * 100), upper_bound))
    tilt = max(lower_bound, min(int(tilt * 100), upper_bound))
    D1_6 = np.array([pan, tilt, 0], dtype=np.int16).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def set_zoom(Byte1):
    ''' zoom
        Byte1=1：Zoom in
        Byte1=2：Zoom out
        Byte1=3：Stop
        Byte1=4：ZOOM=1
        Byte1=5：2× Zoom in
        Byte1=6：2× Zoom out
    '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x12
    lower_bound, upper_bound = 1, 6
    d1 = max(lower_bound, min(int(Byte1), upper_bound))
    D1_6 = np.array([d1, 0, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum


def set_snapshot(Byte1, Byte2):
    ''' snapshot
        Byte1：
            0x01: single shot
            0x02: continuous shooting
            0x03: time-lapse shooting
            0x04: timed shot
            0x05: Stop shooting.
        Byte2：
            If Byte1= 0x02, Byte2= Number of continuous shots
            If Byte1= 0x03, Byte2= Delayed time (Sec)
            If Byte1= 0x04, Byte2= Timed time (Sec)
        '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x10
    lower_bound, upper_bound = 1, 5
    D1 = max(lower_bound, min(int(Byte1), upper_bound))
    lower_bound, upper_bound = 0, 255
    D2 = max(lower_bound, min(int(Byte2), upper_bound))
    D1_6 = np.array([D1, D2, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def set_yaw(angle):
    ''' yaw
        Byte1=1：
        Byte2-3: Angle of Yaw*10[0,3600] 2 Low 3 High
        '''
    # return # todo this is not working JN
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x08
    lower_bound, upper_bound = 0, 3600
    angle = max(lower_bound, min(int(angle*10), upper_bound))
    [low_byte, high_byte] = int16_to_bytes(angle)
    print(f"{low_byte = } {high_byte = } {angle = }")
    D1_6 = np.array([1, low_byte, high_byte, 1, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def set_pitch(angle):
    ''' pitch
        Byte1=2：
        Byte2-3: Angle of Pitch *10[-1000,600]  2 Low 3 High；
    '''

    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x08
    lower_bound, upper_bound = -1000, 600
    angle = max(lower_bound, min(int(angle*10), upper_bound))
    [low_byte, high_byte] = int16_to_bytes(angle)
    D1_6 = np.array([2, low_byte, high_byte, 1, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def set_oneKeyDown():
    ''' point down
        '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x07
    D1_6 = np.array([0, 0, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def set_forward():
    ''' point down
        '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x02
    D1_6 = np.array([0, 0, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def set_quickCalibration():
    ''' point down
    0xF0: Quick Calibration
        '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0xF0
    D1_6 = np.array([0, 0, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum


def set_trackingStop():
    ''' Tracking stop
        '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x06
    D1_6 = np.array([0, 0, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum
