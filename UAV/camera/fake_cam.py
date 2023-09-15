# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/api/30_camera.fake.ipynb.

# %% auto 0
__all__ = ['create_toml_file', 'read_camera_dict_from_toml', 'CameraCaptureStatus', 'CV2Camera', 'GSTCamera', 'airsimCamera',
           'videoCamera']

# %% ../../nbs/api/30_camera.fake.ipynb 6
import time, os, sys

from ..logging import logging
from ..mavlink.mavcom import MAVCom, time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
from ..mavlink.component import Component, mavutil, mavlink, MAVLink
from ..mavlink.camera import BaseCamera
import threading
import cv2
import numpy as np
try:
    # https://hackernoon.com/how-to-manage-configurations-easily-using-toml-files
    import tomllib   # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib
import tomli_w

# from UAV.imports import *   # TODO why is this relative import on nbdev_export?
from fs.memoryfs import MemoryFS
from dataclasses import dataclass

# %% ../../nbs/api/30_camera.fake.ipynb 8
def create_toml_file(filename):
    """Create a TOML file for testing."""
    camera_info = {
        'vendor_name': 'John Doe                   ',  # >= 32 bytes
        'model_name': 'Fake Camera                  ', # >= 32 bytes
        'firmware_version': 1,
        'focal_length': 8.0,   # mm
        'sensor_size_h': 6.0,  # mm
        'sensor_size_v': 4.0,  # mm
        'resolution_h': 1920,
        'resolution_v': 1080,
        'lens_id': 0,
        'flags': 0,
        'cam_definition_version': 1,
        'cam_definition_uri': 'http://example.com/camera_definition.xml',
    }
    # Camera postion relative the vehicle body frame
    camera_position = {
        'x': 0.0,
        'y': 0.0,
        'z': 0.0,
        'roll': 0.0,
        'pitch': 0.0,
        'yaw': 0.0,
    }
    # GStreamer pipeline for video streaming and image capturing
    gstreamer = {
        'pipeline':[
            'videotestsrc pattern=ball flip=true is-live=true num-buffers=1000 ! video/x-raw,framerate=10/1 !  tee name=t',
            't.',
            'queue leaky=2 ! valve name=myvalve drop=False ! video/x-raw,format=I420,width=640,height=480',
            # 'textoverlay text="Frame: " valignment=top halignment=left shaded-background=true',
            # 'timeoverlay valignment=top halignment=right shaded-background=true',
            'videoconvert',
            # 'x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast',
            'x264enc tune=zerolatency',
            'rtph264pay ! udpsink host=127.0.0.1 port=5000',
            't.',
            'queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=5/1,format=(string)BGR',
            'videoconvert ! appsink name=mysink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
        ]}
    
    camera_dict = {
        'camera_info': camera_info,
        'camera_position': camera_position,
        'gstreamer': gstreamer,
    }
    with open(filename, "wb") as f:
        tomli_w.dump(camera_dict, f)



# %% ../../nbs/api/30_camera.fake.ipynb 11
def read_camera_dict_from_toml(toml_file_path # path to TOML file
                               )->dict: # camera_info dict
    """Read MAVLink camera info from a TOML file."""
    with open(toml_file_path, 'rb') as file:
        camera_dict = tomllib.load(file)
        return camera_dict

@dataclass
class CameraCaptureStatus:
    time_boot_ms: int = 0
    image_status: int = 0
    video_status: int = 0
    image_interval: int = 0
    recording_time_ms: int = 0
    available_capacity: int = 0
    image_count: int = 0

# %% ../../nbs/api/30_camera.fake.ipynb 12
class CV2Camera(BaseCamera):
    """Create a fake camera component for testing"""
    def __init__(self, mav=None, # MAVLink connection
                 camera_dict=None, # camera_info dict
                 debug=False): # debug log flag
        super().__init__(mav, camera_dict)
        self.mav:MAVLink = mav
        if camera_dict is not None:
            self.camera_info = self.get_camera_info(camera_dict)   # camera_info dict
        else:
            self.camera_info = None

        assert self.camera_info is not None and len(self.camera_info) > 0, "camera_info is empty"

        self.camera_capture_status = CameraCaptureStatus()
        # self.interval = 1
        # self.max_count = 0
        self.current_img_cnt = 0

        # self.image_filename = ""
        self._log = logging.getLogger("uav.{}".format(self.__class__.__name__))
        self._log.setLevel(logging.DEBUG if debug else logging.INFO)

        self.capture_thread = threading.Thread(target=self.capture_image_thread)
        self.mem_fs = MemoryFS()
        self.fs_size = 100000000  # 100MB

        self.log.info(f"{self.__class__.__name__} Started")
        # todo add settings file
        # read parameters from settings file  # todo add settings file

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return "<{}>".format(self)

    @property
    def log(self) -> logging.Logger:
        return self._log



    def save_image_to_memoryfs(self, img, filename):
        # Convert OpenCV image to JPEG byte stream
        success, buffer = cv2.imencode(".jpg", img)
        if not success:
            raise ValueError("Failed to encode image")

        # Write to PyFilesystem's Memory Filesystem
        with self.mem_fs.open(filename, "wb") as f:
            f.write(buffer.tobytes())

        print(f"Image saved to memory filesystem with name: {filename}")
        # return mem_fs

    def calculate_memory_usage(self):
        """Calculate total memory used by the MemoryFS."""
        total_memory = 0
        for path in self.mem_fs.walk.files():
            with self.mem_fs.open(path, "rb") as f:
                total_memory += len(f.read())
        return total_memory


    def camera_settings_send(self):
        """ Information about a camera. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_SETTINGS
        self.mav.camera_settings_send(time_since_boot_ms(),  # time_boot_ms
                                            0,   # mode_id (int)
                                            0,    # zoomLevel (float)
                                            0,    # focusLevel (float)
                                         )

    def storage_information_send(self):
        """ Information about a camera. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_STORAGE_INFORMATION
        self.mav.storage_information_send(time_since_boot_ms(),  # time_boot_ms
                                            0,   # storage_id
                                            1,    # storage_count
                                            0,    # status
                                            self.fs_size,    # total_capacity
                                            self.calculate_memory_usage(),    # used_capacity
                                            self.fs_size-self.calculate_memory_usage(),    # available_capacity
                                            0,    # read_speed
                                            0,    # write_speed
                                         )

    def camera_capture_status_send(self):
        """ Information about a camera. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS
        ccs = self.camera_capture_status
        self.mav.camera_capture_status_send(time_since_boot_ms(),  # time_boot_ms
                                            ccs.image_status,   # image_status
                                            ccs.video_status,    # video_status
                                            ccs.image_interval,    # image_interval
                                            ccs.recording_time_ms,    # recording_time_ms
                                            ccs.video_status,    # available_capacity
                                            ccs.image_count,    # image_count
                                         )

    def camera_image_captured_send(self):
        if self.mav is not None:
            self.mav.camera_image_captured_send(time_since_boot_ms(),  # time_boot_ms
                                                time_UTC_usec(),  # time_utc
                                                0,  # camera_id
                                                0,  # lat
                                                0,  # lon
                                                0,  # alt
                                                0,  # relative_alt
                                                [0, 0, 0, 0],  # q
                                                self.camera_capture_status.image_count,  # image_index
                                                1,  # capture_result
                                                bytes(self.image_filename, 'utf-8'),  # file_url
                                                )

    def image_start_capture(self, interval, # Image capture interval
                            count, # Number of images to capture (0 for unlimited)
                            ):
        """Start image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        # self.interval = interval
        self.camera_capture_status.image_interval = interval
        self.max_count = count
        self.capture_thread.start()

    def get_next_image(self, filename):
        """Get next image from camera. Simulate an image capture using OpenCV"""
        image = np.zeros((512, 512, 3), dtype=np.uint8)
        cv2.putText(image, "Fake Image", (50, 256), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)

        self.save_image_to_memoryfs(image, filename)

    def time_UTC_usec(self):
        return int(time.time() * 1e6)

    def capture_image_thread(self):
        self._capture_images_thread_running = True
        current_img_cnt = 0
        while self._capture_images_thread_running:
            self.image_filename = f"{date_time_str()}_{self.camera_capture_status.image_count:04d}.jpg"
            img = self.get_next_image(self.image_filename)

            # print(f"Captured image")

            if self.mav is not None:
                self.mav.camera_image_captured_send(time_since_boot_ms(), # time_boot_ms
                                                    time_UTC_usec(), # time_utc
                                                    0, # camera_id
                                                    0, # lat
                                                    0, # lon
                                                    0, # alt
                                                    0, # relative_alt
                                                    [0,0,0,0], # q
                                                    self.camera_capture_status.image_count, # image_index
                                                    1, # capture_result
                                                    bytes(self.image_filename, 'utf-8'), # file_url
                                                    )

            if current_img_cnt >= self.max_count:
                self._capture_images_thread_running = False

            current_img_cnt += 1
            self.camera_capture_status.image_count += 1


            time.sleep(self.camera_capture_status.image_interval)
    def close(self):
        self._capture_images_thread_running = True
        if self.capture_thread.is_alive():
            self.capture_thread.join()
        self.log.info(f"{self.__class__.__name__} closed")

    def __enter__(self):
        """ Context manager entry point for with statement."""
        return self  # This value is assigned to the variable after 'as' in the 'with' statement

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point."""
        self.close()
        return False  # re-raise any exceptions


    # def camera_capture_status_send(self, time_boot_ms, image_status, video_status, image_interval, recording_time_ms, available_capacity, image_count):
    #     msg = self.mav.mav.camera_capture_status_encode(time_boot_ms, image_status, video_status, image_interval, recording_time_ms, available_capacity, image_count)
    #     self.mav.mav.send(msg)
    

# %% ../../nbs/api/30_camera.fake.ipynb 13
from gstreamer import GstVidSrcValve
import gstreamer.utils as gst_utils

# %% ../../nbs/api/30_camera.fake.ipynb 14
class GSTCamera(CV2Camera):

    def __init__(self, mav=None,  # MAVLink connection
                 camera_dict=None,  # camera_info dict
                 debug=False):  # debug log flag
        super().__init__(mav, camera_dict, debug)

        pipeline = gst_utils.to_gst_string(camera_dict['gstreamer']['pipeline'])
        self.pipeline = GstVidSrcValve(pipeline, leaky=True)
        self.pipeline.startup()
        self.last_image = None
        pass

    def get_next_image(self, filename):
        """Get next image from camera using GStreamer."""
        buffer = self.pipeline.pop()
        if not buffer:
            print("No buffer")
        else:
            self.save_image_to_memoryfs(buffer.data, self.image_filename)
            self.last_image = buffer.data


    def close(self):
        self.pipeline.shutdown()
        super().close()


# %% ../../nbs/api/30_camera.fake.ipynb 26
def airsimCamera(camera_name):
    """
    Set up streaming pipeline for Airsim camera
    """
    return True


# %% ../../nbs/api/30_camera.fake.ipynb 27
def videoCamera(camera_name):
    """
    Set up streaming pipeline for Video camera
    """
    return True


# %% ../../nbs/api/30_camera.fake.ipynb 28
def videoCamera(camera_name):
    """
    Set up streaming pipeline for Video camera
    """
    return True


# %% ../../nbs/api/30_camera.fake.ipynb 29
def videoCamera(camera_name):
    """
    Set up streaming pipeline for Video camera
    """
    return True

