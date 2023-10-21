import time

from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil, mavlink
from UAV.utils import start_displays
from UAV.utils.general import boot_time_str, With, toml_load, config_dir

from UAV.camera.gst_cam import GSTCamera
from gstreamer import GstPipeline, Gst, GstContext, GstPipes

from pathlib import Path
import cv2

if __name__ == '__main__':
    print(f"{boot_time_str =}")
    p = start_displays(num_cams=2, port=5000)
    with GstContext():
        with GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_0.toml"), loglevel=10) as cam:
            cam.play()

            cam.video_start_streaming()
            time.sleep(1)
            cam.pause()
            time.sleep(1)
            cam.play()
            time.sleep(1)
            cam.video_stop_streaming()

            cam.image_start_capture(0.1, 5)
            while cam._gst_image_save.is_active:
                if cam.last_image is not None:
                    pass
                    # cv2.imshow('image', cam_fake1.last_image)
                    # cam_fake1.last_image = None
                cv2.waitKey(10)
            print (f"Waiting for capture thread to finish")

    p.terminate()


