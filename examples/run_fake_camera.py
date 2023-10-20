
from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil, mavlink
from UAV.utils.general import boot_time_str, With, read_camera_dict_from_toml, find_config_dir

from UAV.camera.gst_cam import GSTCamera
from gstreamer import GstPipeline, Gst, GstContext, GstPipes

from pathlib import Path
import cv2

if __name__ == '__main__':
    print (f"{boot_time_str =}")

    with GstContext():
        with  GSTCamera(camera_dict=read_camera_dict_from_toml(find_config_dir() / "test_camera_info.toml"), loglevel=10) as cam_fake1:
            cam_fake1.image_start_capture(0.1, 5)
            while cam_fake1._gst_image_save.is_active:
                if cam_fake1.last_image is not None:
                    pass
                    # cv2.imshow('image', cam_fake1.last_image)
                    # cam_fake1.last_image = None
                cv2.waitKey(10)
            print (f"Waiting for capture thread to finish")




