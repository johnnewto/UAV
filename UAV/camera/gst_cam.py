
__all__ = ['CameraCaptureStatus', 'BaseCamera', 'CaptureThread', 'CV2Camera',
           'GSTCamera', 'create_toml_file']


import time, os, sys
from typing import List

from ..logging import logging, LogLevels
# from ..mavlink.mavcom import MAVCom, time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
from ..utils.general import time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
from ..mavlink.component import Component, mavutil, mavlink, MAVLink
try:
    from gstreamer import GstPipeline, GstVideoSource, GstVideoSave, GstJpegEnc, GstStreamUDP, Gst
    import gstreamer.utils as gst_utils
except:
    print("GStreamer is not installed")
    pass

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
    'src_pipeline':[
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

    'ai_pipeline':[
        'intervideosrc channel=channel_0',
        # 'videotestsrc pattern=ball num-buffers={num_buffers}',
        'videoconvert ! videoscale ! video/x-raw,width={width},height={height},framerate={fps}/1,format=(string)BGR',
        'appsink name=ai_sink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
    ],

    'jpg_pipeline':[
        'intervideosrc channel=channel_1  ',
        # 'videotestsrc pattern=ball num-buffers={num_buffers}',
        'videoconvert ! videoscale ! video/x-raw,width={width},height={height},framerate={fps}/1',
        'queue',
        'jpegenc quality={quality}',  # Quality of encoding, default is 85
        # "queue",
        'appsink name=mysink emit-signals=True max-buffers=1 drop=True',
    ],

    'udp_pipeline':[
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

    
    camera_dict = {
        'camera_info': camera_info,
        'camera_position': camera_position,
        'gstreamer': gstreamer,
    }
    with open(filename, "wb") as f:
        toml.dump(camera_dict, f)




# def read_camera_dict_from_toml(toml_file_path # path to TOML file
#                                )->dict: # camera_info dict
#     """Read MAVLink camera info from a TOML file."""
#     camera_dict = toml.load(toml_file_path)
#     return camera_dict

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
        if camera_dict is  None:
            self.camera_dict = {'camera_info':{
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

        self.camera_info = self.get_camera_info(self.camera_dict)   # camera_info dict

        self.model_name = self.camera_dict['camera_info']['model_name']
        self.mav:MAVLink = None  # camera_server.on_mav_connection() callback sets this  (line 84)
        self.source_system = None # camera_server.on_mav_connection() callback sets this  (line 84)
        self.source_component = None # camera_server.on_mav_connection() callback sets this  (line 84)

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return "<{}>".format(self)
    @property
    def log(self) -> logging.Logger:
        return self._log

    def get_camera_info(self, camera_dict):
        """get  MAVLink camera info from a TOML dict."""
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

        s = str(''.join(chr(i) for i in camera_info['vendor_name']) )
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
        """ Information about a camera. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_INFORMATION
        try:
            self.set_source_compenent()
            self.mav.camera_information_send(time_since_boot_ms(),  # time_boot_ms
                                                self.camera_info['vendor_name'],         # vendor name
                                                self.camera_info['model_name'],          # model name
                                                self.camera_info['firmware_version'],    # firmware version
                                                self.camera_info['focal_length'],        # focal length
                                                self.camera_info['sensor_size_h'],       # sensor size h
                                                self.camera_info['sensor_size_v'],       # sensor size v
                                                self.camera_info['resolution_h'],        # resolution h
                                                self.camera_info['resolution_v'],        # resolution v
                                                self.camera_info['lens_id'],             # lend_id
                                                self.camera_info['flags'],               # flags
                                                self.camera_info['cam_definition_version'],          # cam definition version
                                                bytes(self.camera_info['cam_definition_uri'], 'utf-8'), # cam definition uri
                                             )
            self.log.debug(f"{self.mav.srcSystem = } {self.mav.srcComponent = }")
            self.log.debug(f"camera_information_send {self.camera_info = } {self.mav = }")
        except AttributeError:
            self.log.warning("No mav connection")
            # raise AttributeError

    def close(self) :
        pass


class CaptureThread():
    """Managed the Capture of images or video in a separate thread."""
    def __init__(self, interval=1, max_count=1, on_timer=None, on_stop= None):
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
    """Create a fake camera component for testing"""
    def __init__(self,
                 camera_dict=None, # camera_info dict
                 loglevel=LogLevels.INFO): # log flag
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


    def save_image_to_memoryfs(self, img: np.ndarray, # image to save
                               filename: str): # filename to save image
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
        l  = []
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
        """ Information about a camera. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_SETTINGS
        try:
            self.set_source_compenent()
            self.mav.camera_settings_send(time_since_boot_ms(),  # time_boot_ms
                                                0,   # mode_id (int)
                                                0,    # zoomLevel (float)
                                                0,    # focusLevel (float)
                                             )
        except AttributeError:
            self.log.warning("No mav connection")

    def storage_information_send(self):
        """ Information about a camera. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_STORAGE_INFORMATION
        try:
            self.set_source_compenent()
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
        except AttributeError:
            self.log.warning("No mav connection")

    def camera_capture_status_send(self):
        """ Information about a camera. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS
        ccs = self.camera_capture_status
        try:
            self.set_source_compenent()
            self.mav.camera_capture_status_send(time_since_boot_ms(),  # time_boot_ms
                                                ccs.image_status,   # image_status
                                                ccs.video_status,    # video_status
                                                ccs.image_interval,    # image_interval
                                                ccs.recording_time_ms,    # recording_time_ms
                                                ccs.video_status,    # available_capacity
                                                ccs.image_count,    # image_count
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

    def image_start_capture(self, interval, # Image capture interval
                            count, # Number of images to capture (0 for unlimited)f
                            ):
        """Start image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        # self.interval = interval
        self.camera_capture_status.image_status = 1
        self.camera_capture_status.image_interval = interval
        self.max_count = count
        self._image_capture_thread = CaptureThread(interval=interval, max_count=count, on_timer=self.on_capture_image, on_stop= self.on_stop_image_capture)
        self._image_capture_thread.start()
        self.on_start_image_capture()


    def on_capture_image(self, data):
        """Call back function for Get next image from camera. Simulate an image capture using OpenCV"""
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
    """ Create a fake camera component for testing using GStreamer"""

    def __init__(self,
                 camera_dict=None,  # camera_info dict
                 udp_encoder='H264',  # encoder for video streaming
                 loglevel=LogLevels.INFO):  # log flag
        super().__init__( camera_dict, loglevel)

        self.camera_dict = camera_dict
        self.udp_encoder = udp_encoder
        self._loglevel = loglevel

        self.last_image = None
        self.pipeline = None
        self._open()

    def _open(self):
        """create and start the gstreamer pipeleine for the camera"""
        # check to see if attribute pipeline exists

        if self.pipeline is None:
            command = gst_utils.to_gst_string(self.camera_dict['gstreamer']['src_pipeline'])
            self.pipeline = GstPipeline(command, loglevel=self._loglevel)
            self.pipeline.startup()
            return self
        else:
            self.log.warning("Pipeline already exists")
            return self

    def pause(self):
        """ Pause the gstreamer pipeline"""
        self.pipeline.pipeline.set_state(Gst.State.PAUSED)

    def play(self):
        """ Play the gstreamer pipeline"""
        self.pipeline.pipeline.set_state(Gst.State.PLAYING)

    def save_image_to_memoryfs(self, data: bytes, # jpeg encoded image to save
                               filename: str): # filename to save image
        """Save image to memory filesystem."""
        with self.mem_fs.open(filename, "wb") as f:
            f.write(data) # Write to PyFilesystem's Memory Filesystem
        self.log.info(f"Image saved to memory filesystem with name: {filename}")

    def load_image_from_memoryfs(self, filename: str): # filename to load image
        """Load image from memory filesystem."""
        with self.mem_fs.open(filename, "rb") as f:
            data = f.read()
            # convert to jpeg to numpy array
            img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        return img

    def on_capture_image(self, data):
        """Call back function from the CaptureThread (images). Gets the next image from camera using GStreamer."""
        self.image_filename = f"{date_time_str()}_{self.camera_capture_status.image_count:04d}.jpg"
        self.save_image_to_memoryfs(data, self.image_filename)
        self.last_image = data
        self.camera_capture_status.image_count += 1
        self.camera_image_captured_send()

    def image_start_capture(self, interval, # Image capture interval
                            count, # Number of images to capture (0 for unlimited)
                            ):
        """Start image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        # self.interval = interval
        self.camera_capture_status.image_status = 1
        self.camera_capture_status.image_interval = interval
        self.max_count = count

        pipeline = gst_utils.to_gst_string(self.camera_dict['gstreamer']['jpg_pipeline'])
        MAX_FPS = 10
        interval = 1/MAX_FPS if interval < 1/MAX_FPS else interval
        fps = int(1/interval)
        pipeline = gst_utils.fstringify(pipeline, quality=85, num_buffers=100, width=640, height=480, fps=fps) # todo add settings file
        self._gst_image_save:GstJpegEnc = GstJpegEnc(pipeline, max_count=count,
                                                     on_jpeg_capture=self.on_capture_image,
                                                     loglevel=self._loglevel).startup()

    def image_stop_capture(self):
        """Stop image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
        self.camera_capture_status.image_status = 0
        try:
            self._gst_image_save.shutdown()
        except Exception as e:
            self.log.error(e)

    def on_video_callback(self):
        """Call back function from the GstStreamUDP Thread (video)."""
        pass

    def video_start_streaming(self, port=5000): # Stream ID (0 for all streams
        """Start video streaming."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_STREAMING
        if '264' in self.udp_encoder:
            pipeline = gst_utils.to_gst_string(self.camera_dict['gstreamer']['h264_pipeline'])
        else:
            pipeline = gst_utils.to_gst_string(self.camera_dict['gstreamer']['raw_pipeline'])
        pipeline = gst_utils.fstringify(pipeline, width=640, height=480, fps=10, port=port)  # todo add settings file
        self._gst_stream_video:GstStreamUDP = GstStreamUDP(pipeline, on_callback=self.on_video_callback, loglevel=self._loglevel).startup()
        self.log.info(f"Video streaming started on port {port}")
        pass

    def video_stop_streaming(self): # Stream ID (0 for all streams
        """Stop video streaming."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_STREAMING
        try:
            self._gst_stream_video.shutdown()
        except Exception as e :
            self.log.warning(f"Video streaming not running {e = }")

    def video_start_capture(self, stream_id, # Stream ID (0 for all streams)
                            frequency): # Frequency CAMERA_CAPTURE_STATUS messages sent (0 for no messages, otherwise frequency)
        """Start video capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_CAPTURE
        self.camera_capture_status.video_status = 1
        interval = None if frequency == 0 else max(1/(frequency+0.000000001), 1) # reporting interval in seconds
        i= 1
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
        try:
            self.pipeline.shutdown(eos=True) # send EOS event to all sinks
        except AttributeError as e:
            # class name
            self.log.error(f"Check that you called {self.__class__.__name__}.open(): {e}")
        super().close()




