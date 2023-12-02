__all__ = ['CameraCaptureStatus', 'BaseCamera', 'CaptureThread', 'CV2Camera',
           'GSTCamera']

import os
import sys
import time
from typing import List

from ..logging import logging, LogLevels
from ..mavlink.component import MAVLink
from ..utils.general import time_since_boot_ms, time_UTC_usec, date_time_str

try:
    from gstreamer import GstPipeline, GstVideoSource, GstVideoSave, GstJpegEnc, GstStreamUDP, Gst
    import gstreamer.utils as gst_utils
except:
    print("GStreamer is not installed")

import threading
import cv2
import numpy as np
# try:
#     # https://hackernoon.com/how-to-manage-configurations-easily-using-toml-files
#     import tomllib   # Python 3.11+
# except ModuleNotFoundError:
#     import tomli as tomllib
# import tomli_w
import toml

# from UAV.imports import *   # TODO why is this relative import on nbdev_export?
from fs.memoryfs import MemoryFS
from dataclasses import dataclass


def todo_remove_create_toml_file(filename):  # todo remove
    """Create a TOML file for testing."""
    camera_info = {
        'vendor_name': 'John Doe                   ',  # >= 32 bytes
        'model_name': 'Fake Camera                  ',  # >= 32 bytes
        'firmware_version': 1,
        'focal_length': 8.0,  # mm
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
    gstreamer_video_src = {
        'width': 640,
        'height': 480,
        'fps': 10,

        'pipeline': [
            #    "videotestsrc pattern=ball is-live=true ! video/x-raw,framerate=10/1 !  autovideosink",
            "videotestsrc pattern=ball is-live=true ! video/x-raw,width=640,height=480,framerate=30/1 !  tee name=t",

            "t.",
            'queue ! autovideosink',

            "t.",
            'queue leaky=2 ! intervideosink channel=channel_0',

            "t.",
            'queue leaky=2 ! intervideosink channel=channel_1',

            "t.",
            'queue leaky=2 ! videoconvert ! videorate drop-only=true ! intervideosink channel=channel_2 ',

        ],
    }

    gstreamer_ai_appsink = {
        'width': 640,
        'height': 480,
        'fps': 10,

        'pipeline': [
            'intervideosrc channel=channel_0',
            # 'videotestsrc pattern=ball num-buffers={num_buffers}',
            'videoconvert ! videoscale ! video/x-raw,width={width},height={height},framerate={fps}/1,format=(string)BGR',
            'appsink name=ai_sink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
        ],
    }

    gstreamer_jpg_filesink = {
        'width': 640,
        'height': 480,
        'fps': 10,

        'pipeline': [
            'intervideosrc channel=channel_1  ',
            # 'videotestsrc pattern=ball num-buffers={num_buffers}',
            'videoconvert ! videoscale ! video/x-raw,width={width},height={height},framerate={fps}/1',
            'queue',
            'jpegenc quality={quality}',  # Quality of encoding, default is 85
            # "queue",
            'appsink name=mysink emit-signals=True max-buffers=1 drop=True',
        ],
    }
    gstreamer_udpsink = {
        'width': 640,
        'height': 480,
        'fps': 10,
        'pipeline': [
            'intervideosrc channel=channel_2',
            # 'videotestsrc pattern=ball flip=true is-live=true ! video/x-raw,framerate={fps}/1',
            'queue',
            'videoscale ! video/x-raw,width={width},height={height},framerate={fps}/1',
            # 'video/x-raw,format=I420,width={width},height={height}',
            # 'queue leaky=2 ! video/x-raw,format=I420,width={width},height={height}',
            # 'videoconvert',
            # 'queue',
            # 'x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast',
            'x264enc tune=zerolatency',
            'rtph264pay ! udpsink host=127.0.0.1 port={port}',
        ],
    }

    gstreamer_raw_udpsink = {
        'width': 640,
        'height': 480,
        'fps': 10,

        'pipeline': [
            'intervideosrc channel=channel_2',
            # 'videotestsrc pattern=ball flip=true is-live=true ! video/x-raw,framerate={fps}/1',
            'queue',
            #            'videoscale ! video/x-raw,format=RGB,width={width},height={height},framerate={fps}/1',
            #            'videoscale'
            #            'videoconvert ! videoscale ! video/x-raw,format=RGB,depth=8,width={width},height={height}',
            'videoconvert ! videoscale ! video/x-raw,format=RGB,depth=8,width=1920,height=1080',
            'rtpvrawpay ! udpsink host=127.0.0.1 port={port}',
            #            'videoconvert ! videoscale ! video/x-raw,format=RGB,depth=8,width=640,height=480 ',
            #            'rtpvrawpay ! udpsink host=127.0.0.1 port=5100',
        ]
    }

    camera_dict = {
        'camera_info': camera_info,
        'camera_position': camera_position,
        'gstreamer_video_src': gstreamer_video_src,
        'gstreamer_ai_appsink': gstreamer_ai_appsink,
        'gstreamer_jpg_filesink': gstreamer_jpg_filesink,
        'gstreamer_raw_udpsink': gstreamer_raw_udpsink,
    }
    with open(filename, "wb") as f:
        toml.dump(camera_dict, f)


@dataclass
class CameraCaptureStatus:
    time_boot_ms: int = 0
    image_status: int = 0
    video_status: int = 0
    image_interval: int = 0
    recording_time_ms: int = 0
    available_capacity: int = 0
    image_count: int = 0

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return "<{}>".format(self)


class BaseCamera:
    def __init__(self,
                 camera_dict=None,  # camera_info dict
                 loglevel=LogLevels.INFO):  # debug log flag
        if camera_dict is None:
            self.camera_dict = {'camera_info': {
                'vendor_name': 'UAV',
                'model_name': 'FakeCamera',
                'firmware_version': 1,
                'focal_length': 2.8,
                'sensor_size_h': 3.2,
                'sensor_size_v': 2.4,
                'resolution_h': 640,
                'resolution_v': 480,
                'lens_id': 0,
                'flags': 0,
                'cam_definition_version': 1,
                'cam_definition_uri': '',
            }}
        else:
            self.camera_dict = camera_dict
        self._loglevel = loglevel
        self._log = logging.getLogger("uav.{}".format(self.__class__.__name__))
        self._log.setLevel(int(loglevel))

        self.camera_info = self.get_camera_info(self.camera_dict)  # camera_info dict

        self.model_name = self.camera_dict['camera_info']['model_name']
        self.mav: MAVLink = None  # camera_server.on_mav_connection() callback sets this  (line 84)
        self.source_system = None  # camera_server.on_mav_connection() callback sets this  (line 84)
        self.source_component = None  # camera_server.on_mav_connection() callback sets this  (line 84)

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return "<{}>".format(self)

    @property
    def log(self) -> logging.Logger:
        return self._log

    def get_camera_info(self, camera_dict):
        """get  MAVLink cameras info from a TOML dict."""

        def make_length_32(s: str) -> str:
            if len(s) > 32:
                return s[:32]
            return s.ljust(32)  # pad with spaces to the right to make length 32

        camera_info = camera_dict['camera_info']
        # vender name and model name must be 32 bytes long
        camera_info['vendor_name'] = make_length_32(camera_info['vendor_name'])
        camera_info['model_name'] = make_length_32(camera_info['model_name'])
        camera_info['vendor_name'] = [int(b) for b in camera_info['vendor_name'].encode()]
        camera_info['model_name'] = [int(b) for b in camera_info['model_name'].encode()]

        s = str(''.join(chr(i) for i in camera_info['vendor_name']))
        print(s)

        return camera_info

    def set_source_compenent(self):
        """Set the source component for the self.mav """
        try:
            self.mav.srcSystem = self.source_system
            self.mav.srcComponent = self.source_component
        except AttributeError:
            self.log.debug("No mav connection")
            # raise AttributeError

    def camera_information_send(self):
        """ Information about a cameras. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_INFORMATION
        try:
            self.set_source_compenent()
            self.mav.camera_information_send(time_since_boot_ms(),  # time_boot_ms
                                             self.camera_info['vendor_name'],  # vendor name
                                             self.camera_info['model_name'],  # model name
                                             self.camera_info['firmware_version'],  # firmware version
                                             self.camera_info['focal_length'],  # focal length
                                             self.camera_info['sensor_size_h'],  # sensor size h
                                             self.camera_info['sensor_size_v'],  # sensor size v
                                             self.camera_info['resolution_h'],  # resolution h
                                             self.camera_info['resolution_v'],  # resolution v
                                             self.camera_info['lens_id'],  # lend_id
                                             self.camera_info['flags'],  # flags
                                             self.camera_info['cam_definition_version'],  # cam definition version
                                             bytes(self.camera_info['cam_definition_uri'], 'utf-8'),  # cam definition uri
                                             )
            self.log.debug(f"{self.mav.srcSystem = } {self.mav.srcComponent = }")
            self.log.debug(f"camera_information_send {self.camera_info = } {self.mav = }")
        except AttributeError:
            self.log.warning("No mav connection")
            # raise AttributeError

    def close(self):
        pass


class CaptureThread():
    """Managed the Capture of images or video in a separate thread."""

    def __init__(self, interval=1, max_count=1, on_timer=None, on_stop=None):
        self._thread = None
        self._stop_event = threading.Event()
        self.interval = interval
        self.max_count = sys.maxsize if max_count is None else max_count
        self.on_timer = on_timer
        self.on_stop = on_stop

    def _run(self):
        current_img_cnt = 0
        while not self._stop_event.is_set():
            if self.on_timer is not None:
                self.on_timer(data=None)
            if current_img_cnt >= self.max_count:  # quit the thread
                self._stop_event.set()
                break
            current_img_cnt += 1
            time.sleep(self.interval)
            print("%%%%%%%%%%%%%%%%")

        if self.on_stop is not None:
            self.on_stop()

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run)
            self._thread.start()
        else:
            print("Thread is already running.")

    def stop(self):
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join()

    def is_running(self):
        return self._thread.is_alive() if self._thread else False


class CV2Camera(BaseCamera):
    """Create a fake cameras component for testing"""

    def __init__(self,
                 camera_dict=None,  # camera_info dict
                 loglevel=LogLevels.INFO):  # log flag
        super().__init__(camera_dict, loglevel)
        # self.mav:MAVLink = mav
        # if camera_dict is not None:
        #     self.camera_info = self.get_camera_info(camera_dict)   # camera_info dict
        # else:
        #     self.camera_info = None
        # self.camera_dict = camera_dict
        assert self.camera_info is not None and len(self.camera_info) > 0, "camera_info is empty"

        self.camera_capture_status = CameraCaptureStatus()
        # self.interval = 1
        # self.max_count = 0
        self.current_img_cnt = 0
        self._image_capture_thread = None
        self._video_capture_thread = None

        # self.image_filename = ""

        self.last_image = None
        self.mem_fs = MemoryFS()
        self.fs_size = 100000000  # 100MB

        self.log.info(f"{self.__class__.__name__} Started")
        # todo add settings file
        # read parameters from settings file  # todo add settings file

    def save_image_to_memoryfs(self, img: np.ndarray,  # image to save
                               filename: str):  # filename to save image
        """Save image to memory filesystem."""
        # Convert OpenCV image to JPEG byte stream
        success, buffer = cv2.imencode(".jpg", img)
        if not success:
            raise ValueError("Failed to encode image")

        # Write to PyFilesystem's Memory Filesystem
        with self.mem_fs.open(filename, "wb") as f:
            f.write(buffer.tobytes())

        self.log.info(f"Image saved to memory filesystem with name: {filename}")
        # return mem_fs

    def calculate_memory_usage(self):
        """Calculate total memory used by the MemoryFS."""
        total_memory = 0
        for path in self.mem_fs.walk.files():
            with self.mem_fs.open(path, "rb") as f:
                total_memory += len(f.read())
        return total_memory

    def list_files(self) -> List:
        """List all files in the MemoryFS."""
        l = []
        for path in self.mem_fs.walk.files():
            l.append(path)
        return l

    def show_image(self, filename=None):
        """Show image using OpenCV."""
        if filename is None:
            filename = self.list_files()
        with self.mem_fs.open(filename, "rb") as f:
            img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_COLOR)
        #     cv2.imshow('image', img)
        # cv2.waitKey(1)

    def camera_settings_send(self):
        """ Information about a cameras. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_SETTINGS
        try:
            self.set_source_compenent()
            self.mav.camera_settings_send(time_since_boot_ms(),  # time_boot_ms
                                          0,  # mode_id (int)
                                          0,  # zoomLevel (float)
                                          0,  # focusLevel (float)
                                          )
        except AttributeError:
            self.log.warning("No mav connection")

    def storage_information_send(self):
        """ Information about a cameras. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_STORAGE_INFORMATION
        try:
            self.set_source_compenent()
            self.mav.storage_information_send(time_since_boot_ms(),  # time_boot_ms
                                              0,  # storage_id
                                              1,  # storage_count
                                              0,  # status
                                              self.fs_size,  # total_capacity
                                              self.calculate_memory_usage(),  # used_capacity
                                              self.fs_size - self.calculate_memory_usage(),  # available_capacity
                                              0,  # read_speed
                                              0,  # write_speed
                                              )
        except AttributeError:
            self.log.warning("No mav connection")

    def camera_capture_status_send(self):
        """ Information about a cameras. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS
        ccs = self.camera_capture_status
        try:
            self.set_source_compenent()
            self.mav.camera_capture_status_send(time_since_boot_ms(),  # time_boot_ms
                                                ccs.image_status,  # image_status
                                                ccs.video_status,  # video_status
                                                ccs.image_interval,  # image_interval
                                                ccs.recording_time_ms,  # recording_time_ms
                                                ccs.video_status,  # available_capacity
                                                ccs.image_count,  # image_count
                                                )
        except AttributeError:
            self.log.warning("No mav connection")

    def camera_image_captured_send(self):
        # check to see if attribute mav is set
        try:
            self.set_source_compenent()
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
        except AttributeError:
            self.log.debug("No mav connection")

    def image_start_capture(self, interval,  # Image capture interval
                            count,  # Number of images to capture (0 for unlimited)f
                            ):
        """Start image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        # self.interval = interval
        self.camera_capture_status.image_status = 1
        self.camera_capture_status.image_interval = interval
        self.max_count = count
        self._image_capture_thread = CaptureThread(interval=interval, max_count=count, on_timer=self.on_capture_image, on_stop=self.on_stop_image_capture)
        self._image_capture_thread.start()
        self.on_start_image_capture()

    def on_capture_image(self, data):
        """Call back function for Get next image from cameras. Simulate an image capture using OpenCV"""
        self.image_filename = f"{date_time_str()}_{self.camera_capture_status.image_count:04d}.jpg"
        image = np.zeros((512, 512, 3), dtype=np.uint8)
        cv2.putText(image, "Fake Image", (50, 256), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
        self.save_image_to_memoryfs(image, self.image_filename)
        self.camera_capture_status.image_count += 1
        self.camera_image_captured_send()
        self.last_image = image

    def on_start_image_capture(self):
        """Call back function when image capture thread is started."""
        pass

    def on_stop_image_capture(self):
        """Call back function when image capture thread is stopped."""
        pass

    def image_stop_capture(self):
        """Stop image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
        self.camera_capture_status.image_status = 0
        self._image_capture_thread.stop()

    def time_UTC_usec(self):
        return int(time.time() * 1e6)

    def image_capture_thread_is_running(self):
        return self._image_capture_thread.is_running()

    def close(self):
        if self._image_capture_thread is not None:
            self._image_capture_thread.stop()
        if self._video_capture_thread is not None:
            self._video_capture_thread.stop()

        self.log.info(f"{self.__class__.__name__} closed")

    def __enter__(self):
        """ Context manager entry point for with statement."""
        return self  # This value is assigned to the variable after 'as' in the 'with' statement

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point."""
        self.close()
        return False  # re-raise any exceptions


class GSTCamera(CV2Camera):
    """ Create a fake cameras component for testing using GStreamer"""

    def __init__(self,
                 config_dict,  # config dict
                 camera_dict=None,  # camera_info dict
                 udp_encoder='h264',  # encoder for video streaming
                 loglevel=LogLevels.INFO):  # log flag
        super().__init__(camera_dict, loglevel)

        # camera_dict = replace_star_text(camera_dict, config_dict)
        self.set_config_values(camera_dict, config_dict)
        # print(camera_dict)

        self.config_dict = config_dict
        self.camera_dict = camera_dict
        self.udp_encoder = udp_encoder
        self.cam_name = self.camera_dict['cam_name']

        self._loglevel = loglevel
        self.last_image = None
        self.pipeline = None
        self._open()
        self._setup_video_stream()

    def _open(self):
        """create and start the gstreamer pipeleine for the cameras"""
        # check to see if attribute pipeline exists

        if self.pipeline is None:
            _dict = self.camera_dict['gstreamer_video_src']
            _dict['cam_name'] = self.cam_name
            # width, height, fps, loglevel = _dict['width'], _dict['height'], _dict['fps'], _dict['loglevel']
            pipeline = gst_utils.format_pipeline(**_dict)

            self.pipeline = GstPipeline(pipeline, loglevel=self._loglevel)
            self.pipeline.startup()
            self.pipeline.pipeline.set_name('gstreamer_video_src')
            # self.pause()
            return self
        else:
            self.log.warning("Pipeline already exists")
            return self

    def set_config_values(self, camera_dict, config_dict):
        """Replace '*....*' parameters in camera_dict with values from config_dict."""
        for key in camera_dict.keys():
            val = camera_dict[key]
            if isinstance(val, str) and val.startswith('*') and val.endswith('*'):
                # replace *...* with value from config_dict
                try:
                    old_val = val
                    camera_dict[key] = config_dict[val[1:-1]]
                    self.log.info(f"Setting {old_val[1:-1]} = {camera_dict[key]}")
                except KeyError:
                    self.log.error(f"KeyError: {val} not found in config_dict")
                    raise KeyError

        for key in camera_dict:
            if isinstance(camera_dict[key], dict):
                self.set_config_values(camera_dict[key], config_dict)

    def get_name(self):
        """Get the name of the gstreamer pipeline"""
        return self.pipeline.pipeline.get_name()

    def pause(self):
        """ Pause the gstreamer pipeline"""
        self.pipeline.pipeline.set_state(Gst.State.PAUSED)
        self.log.info(f"{self.get_name()}: paused")
        # self.pipeline.set_valve_state("myvalve", True)
        # if self.pipeline.pipeline.get_state(Gst.CLOCK_TIME_NONE) == Gst.StateChangeReturn.FAILURE:
        #     self.log.error(f"{self.get_name()}: failed to pause")

        # self.log.info(f"{self.get_name()}: paused (using valve element)")
        # print(f"{self.pipeline.pipeline.get_state(Gst.CLOCK_TIME_NONE)}")

    def play(self):
        """ Resume the gstreamer pipeline"""
        # self.pipeline.set_valve_state("myvalve", False)
        self.pipeline.pipeline.set_state(Gst.State.PLAYING)
        self.log.info(f"{self.get_name()}: playing")

    def save_image_to_memoryfs(self, data: bytes,  # jpeg encoded image to save
                               filename: str):  # filename to save image
        """Save image to memory filesystem."""
        with self.mem_fs.open(filename, "wb") as f:
            f.write(data)  # Write to PyFilesystem's Memory Filesystem
        self.log.info(f"Image saved to memory filesystem with name: {filename}")

    def load_image_from_memoryfs(self, filename: str):  # filename to load image
        """Load image from memory filesystem."""
        with self.mem_fs.open(filename, "rb") as f:
            data = f.read()
            # convert to jpeg to numpy array
            img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        return img

    def on_capture_image(self, data):
        """Call back function from the CaptureThread (images). Gets the next image from cameras using GStreamer."""
        self.image_filename = f"{date_time_str()}_{self.camera_capture_status.image_count:04d}.jpg"
        self.save_image_to_memoryfs(data, self.image_filename)
        self.last_image = data
        self.camera_capture_status.image_count += 1
        self.camera_image_captured_send()

    # def old_image_start_capture(self, interval,  # Image capture interval
    #                         count,  # Number of images to capture (0 for unlimited)
    #                         ):
    #     """Start image capture sequence."""
    #     # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
    #     # self.interval = interval
    #     self.camera_capture_status.image_status = 1
    #     self.camera_capture_status.image_interval = interval
    #     self.max_count = count
    #     _dict = self.camera_dict['gstreamer_jpg_filesink']
    #     # width, height, fps, quality  = _dict['width'], _dict['height'], _dict['fps'], _dict['quality']
    #     _dict['fps'] = int(1 / interval) if interval > 0 else _dict['fps']
    #     pipeline = gst_utils.format_pipeline(**_dict)
    #
    #     # fps = int(1 / interval) if interval > 0 else fps
    #     # pipeline = gst_utils.to_gst_string(_dict['pipeline'])
    #     # print(f'{width=}, {height=}, {fps=}')
    #     # pipeline = gst_utils.fstringify(pipeline, width=width, height=height, fps=fps, quality=quality)
    #
    #     # MAX_FPS = 10
    #     # interval = 1/fps if interval < 1/fps else interval
    #     # fps = int(1/interval)
    #
    #     self._gst_image_save: GstJpegEnc = GstJpegEnc(pipeline, max_count=count,
    #                                                   on_jpeg_capture=self.on_capture_image,
    #                                                   loglevel=self._loglevel).startup()
    #
    #
    #

    def _last_image_index(self, usb_drive_path: str, _filter='jpg'):
        drive_contents = os.listdir(usb_drive_path)
        cam0_files = [file for file in drive_contents if file.endswith(_filter)]
        # # find the highest index based on number after '_' in the filename
        # highest_index = cam0_files[-1].split('_')[1] if cam0_files else 0
        highest_index = cam0_files[-1].split('.')[0] if cam0_files else 0
        return int(highest_index)

    def image_start_capture(self, interval,  # Image capture interval
                            count,  # Number of images to capture (0 for unlimited)
                            ):
        """Start image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        # self.interval = interval
        self.camera_capture_status.image_status = 1
        self.camera_capture_status.image_interval = interval
        # self.max_count = count
        _dict = self.camera_dict['gstreamer_jpg_filesink']
        # width, height, fps, quality  = _dict['width'], _dict['height'], _dict['fps'], _dict['quality']
        _dict['fps'] = int(1 / interval) if interval > 0 else _dict['fps']
        # _path = _dict['path']
        _drive = '/media/'+os.getlogin()+'/jpgs'
        if not os.path.exists(_drive):
            self.log.error(f"Drive {_drive} does not exist")
            return False
        _path = _drive + '/' + self.cam_name
        if not os.path.exists(_path):
            os.mkdir(_path)

        if os.path.exists(_path):
            _index = self._last_image_index(_path)
            _dict['drive'] = _drive
            _dict['index'] = int(_index) + 1
            _dict['cam_name'] = self.cam_name
            pipeline = gst_utils.format_pipeline(**_dict)
            self._gst_image_save = GstPipeline(pipeline, loglevel=self._loglevel).startup()
            self._gst_image_save.pipeline.set_name('gstreamer_jpg_filesink')
            self.log.info(f'Image capture pipeline "{self._gst_image_save.pipeline.get_name()}" created')
        else:
            self.log.error(f"Path {_path} does not exist")
            return False  # Todo what to return if any

    def image_stop_capture(self):
        """Stop image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
        self.camera_capture_status.image_status = 0
        try:
            self.log.info(f'Image capture pipeline "{self._gst_image_save.pipeline.get_name()}" closing')
            self._gst_image_save.shutdown()
        except Exception as e:
            self.log.error(e)

    def on_video_callback(self):
        """Call back function from the GstStreamUDP Thread (video)."""
        pass

    def _setup_video_stream(self, streamId=0):  # Stream ID (0 for all streams
        """Creates a GStreamer pipeline for streaming video,."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_STREAMING
        self._stream_dict = self.camera_dict['gstreamer_udpsink']
        self._stream_dict['port'] += int(streamId * 10)  # todo fix this port allocation
        # width, height, fps, port  = _dict['width'], _dict['height'], _dict['fps'], _dict['port']
        self._stream_dict['cam_name'] = self.cam_name
        pipeline = gst_utils.format_pipeline(**self._stream_dict)
        self._pipeline_stream_udp: GstStreamUDP = GstStreamUDP(pipeline, on_callback=self.on_video_callback, loglevel=self._loglevel).startup()
        self._pipeline_stream_udp.pipeline.set_name('gstreamer_udpsink')
        self.log.info(f'Video streaming pipeline "{self._pipeline_stream_udp.pipeline.get_name()}" created on port {self._stream_dict["port"]}')
        time.sleep(0.1)
        self.video_stop_streaming()

    def video_start_streaming(self, streamId=0):  # Stream ID (0 for all streams
        """Start video streaming. Creates a GStreamer pipeline for streaming video, if it does not exist otherwise resumes it."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_STREAMING
        self._pipeline_stream_udp.set_valve_state("myvalve", False)
        self.log.info(f'Video streaming "{self._pipeline_stream_udp.pipeline.get_name()}" resumed on port {self._stream_dict["port"]}')

    def video_stop_streaming(self):  # Stream ID (0 for all streams
        """Stop video streaming by pause on gstreamer valve element."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_STREAMING
        self._pipeline_stream_udp.set_valve_state("myvalve", True)
        self.log.info(f'Video streaming "{self._pipeline_stream_udp.pipeline.get_name()}" stopped (paused) on port {self._stream_dict["port"]}')

    def video_start_capture(self, stream_id,  # Stream ID (0 for all streams)
                            frequency):  # Frequency CAMERA_CAPTURE_STATUS messages sent (0 for no messages, otherwise frequency)
        """Start video capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_CAPTURE
        self.camera_capture_status.video_status = 1
        interval = None if frequency == 0 else max(1 / (frequency + 0.000000001), 1)  # reporting interval in seconds
        i = 1
        self._gst_vid_save = GstVideoSave(f'file{i:03d}.mp4', 1280, 720, status_interval=interval, on_status_video_capture=self.on_status_video_capture, loglevel=self._loglevel).startup()

    def on_status_video_capture(self):
        """Call back function when video capture thread ontimer"""
        # print(f"{self.camera_info = }")

        model_name = ''.join([chr(c) for c in self.model_name])
        self.log.info(f'camera_capture_status_send {model_name = }')
        self.camera_capture_status_send()
        pass

    def video_stop_capture(self):
        """Stop video capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_CAPTURE
        self.camera_capture_status.video_status = 0
        self._gst_vid_save.stop()
        # self.pipeline.set_valve_state("video_valve", False)

    def close(self):
        """Close  gstreamer pipelines opened by the cameras"""
        try:
            self.pipeline.shutdown(eos=True)  # send EOS event to all sinks
        except AttributeError as e:
            # class name
            self.log.error(f"Check that you called {self.__class__.__name__}.open(): {e}")
        super().close()
        # trying to fix interpipe gstinterpipe.c:236:gst_inter_pipe_leave_node_priv: Node video_src not found. Could not leave node.
        time.sleep(0.1)  # todo fix this Node video_src not found
        if self._pipeline_stream_udp is not None:
            self._pipeline_stream_udp.shutdown()
            self.log.info(f'!!!!!! Closed "{self._pipeline_stream_udp.pipeline.get_name()}" ')
