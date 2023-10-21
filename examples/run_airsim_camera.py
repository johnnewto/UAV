import time

from UAV.camera.airsim_cam import AirsimCamera
from UAV.logging import LogLevels
from UAV.utils import start_displays
from UAV.utils.general import toml_load, config_dir
from gstreamer import GstContext

# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
if __name__ == '__main__':

    UDP_ENCODER = 'h264'
    # UDP_ENCODER = 'raw-video'
    camera_dict_0 = toml_load(config_dir() / "airsim_cam_0.toml")
    camera_dict_1 = toml_load(config_dir() / "airsim_cam_1.toml")
    p = start_displays(num_cams=2, port=5000)

    with GstContext():
        with AirsimCamera(camera_name='front', camera_dict=camera_dict_0, loglevel=LogLevels.INFO) as air_cam_0:
            with AirsimCamera(camera_name='left', camera_dict=camera_dict_1, loglevel=LogLevels.INFO) as air_cam_1:
                pass
                # air_cam.image_start_capture(0.1, 5)
                # while air_cam._gst_image_save.is_active:
                #     time.sleep(0.1)
                # time.sleep(0)
                # air_cam_0.pause()

                air_cam_0.video_start_streaming()
                air_cam_1.video_start_streaming()
                for i in range(5):
                    air_cam_0.pause()    todo fix pause is not working for airsim camera  GstVideoSink is pushed so does not have pause..
                    air_cam_1.pause()
                    time.sleep(1)
                    air_cam_0.play()
                    air_cam_1.play()
                    time.sleep(1)
                air_cam_0.video_stop_streaming()
                air_cam_1.video_stop_streaming()
                time.sleep(1)
                print(f"Waiting for capture thread to finish")

    p.terminate()
