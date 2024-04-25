__all__ = ['AirsimCamera']

import time

from ..logging import LogLevels
from ..utils import config_dir

try:
    # allow import of gstreamer to fail if not installed (for github actions)
    from gstreamer import GstPipeline, GstVideoSource, GstVideoSave, GstJpegEnc, GstStreamUDP, GstVideoSink
    import gstreamer.utils as gst_utils
except:
    print("GStreamer is not installed")
    pass
from ..cameras.gst_cam import GSTCamera
from ..utils.sim_linux import RunSim
from ..airsim.client import AirSimClient
import threading

# cams = ["high_res", "front_center", "front_right", "front_left", "bottom_center", "back_center"]


class AirsimCamera(GSTCamera):
    """ run the airsim enviroment Create a airsim cameras component for testing using GStreamer"""

    def __init__(self,
                 config_dict,  # config dict
                 camera_dict=None,  # camera_info dict
                 udp_encoder='h264',  # encoder for video streaming
                 loglevel=LogLevels.INFO):  # log flag

        self.camera_name = camera_dict['cam_name']
        _dict = camera_dict['gstreamer_video_src']
        self._dont_wait = threading.Event()  # used to pause or resume the thread

        config_file = config_dir() / "airsim_settings_high_res.json"
        # self.check_airsm_camera_resolution(config_file, camera_name, _dict['width'], _dict['height'])
        self.rs = RunSim("AirSimNH", settings=config_file)
        # time.sleep(1)
        self.asc = AirSimClient()

        self._dont_wait = threading.Event()  # used to pause or resume the thread
        super().__init__(config_dict, camera_dict=camera_dict, udp_encoder=udp_encoder, loglevel=loglevel)
        self.log.info(f"***** AirsimCamera: {self.camera_name = } ******")

    def check_airsm_camera_resolution(self, settings_file_path, camera_name, desired_width, desired_height):
        """check the airsim cameras resolution and update if necessary"""
        import json

        # Read the existing settings.json file
        with open(settings_file_path, 'r') as json_file:
            settings = json.load(json_file)


        camera_settings = settings['Vehicles']['Drone1']['Cameras'].get(camera_name)

        if camera_settings is None:
            raise RuntimeError(f'Error finding cameras "{camera_name}" in {settings_file_path}')
        # Find the cameras section you want to modify
        try:
            # camera_settings = settings['Vehicles']['Drone1']['Cameras'].get(camera_name)
            if camera_settings:
                # Get the current width and height
                current_width = camera_settings['CaptureSettings'][0]['Width']
                current_height = camera_settings['CaptureSettings'][0]['Height']

                # Check if the current resolution is different from the desired resolution
                if current_width != desired_width or current_height != desired_height:
                    # Update the width and height settings
                    camera_settings['CaptureSettings'][0]['Width'] = desired_width
                    camera_settings['CaptureSettings'][0]['Height'] = desired_height

                    # Write the updated settings back to the file
                    with open(settings_file_path, 'w') as json_file:
                        json.dump(settings, json_file, indent=4)
                        self.log.info(f"Updated {camera_name} width and height settings in {settings_file_path}")

        except Exception as e:
            self.log.error(f"Error updating {camera_name} width and height settings in {settings_file_path}: {e}")

    def _open(self):
        """
          Override GSTCamera ._open()
          create and start the gstreamer pipeleine for the cameras
        """
        if hasattr(self, "_running"):
            self.log.error("AirsimCamera is already opened, Check to see if you have called _open() ")
            return self

        _dict = self.camera_dict['gstreamer_video_src']
        _dict['cam_name'] = self.cam_name  # propagate cam_name into _dict
        self.width, self.height, self.fps = _dict['width'], _dict['height'], _dict['fps']
        pipeline = gst_utils.format_pipeline(**_dict)
        self.pipeline = GstVideoSink(pipeline, width=self.width, height=self.height, fps=self.fps, loglevel=self._loglevel)

        self.pipeline.startup()

        self._thread = threading.Thread(target=self.run_pipe, args=[self.camera_name], daemon=True)
        self._thread.start()

        return self

    def run_pipe(self, camera_name):
        """run the cameras pipeline in a thread"""

        self._dont_wait.set()
        framecounter = 1
        self._running = True


        while self._running:
            framecounter += 1
            self._dont_wait.wait()
            # print(f"{framecounter = }")
            try:
                img = self.asc.get_image(camera_name, rgb2bgr=True)
                # self.log.info(f"pushing {camera_name} : {img.shape = } on {self.camera_dict['gstreamer_udpsink']}")

                self.pipeline.push(buffer=img)
                # self.log.info(f"pushed {self.pipeline.pipeline.get_name()}")
                if img.shape != (self.height, self.width, 3):  # numpy array are rows by columns = height by width
                    self.log.error(f"Airsim img.shape = {img.shape} != {(self.height, self.width, 3)}")
            except Exception as e:
                self.log.error(f'Error getting image from Camera "{camera_name}":  {e}')
                time.sleep(0.1)

            time.sleep(1 / self.fps)  # set fps to self.fps  todo use timer to cac  fps as its too slow
            if framecounter % 100 == 0:
                self.log.info(f"Frame: {framecounter} {img.shape = }")

        self.log.debug("Exiting AirsimCamera thread")

    def pause(self):
        """Pause the airsim cameras grab thread ."""
        self._dont_wait.set()  # pause the thread
        super().pause()

    def play(self):
        """Play the airsim cameras grab thread."""
        self._dont_wait.clear()
        super().play()

    def close(self):
        """Close the cameras component."""
        if not hasattr(self, "_running"):
            self.log.error("AirsimCamera was not opened, Check to see if you have called _open() ")
        else:
            self._running = False
        try:
            self.rs.exit()
        except:
            pass
        super().close()

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point."""
        self.log.info("Exiting AirsimCamera")
        super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return False  # re-raise any exceptions
