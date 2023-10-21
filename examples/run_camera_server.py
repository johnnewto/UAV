from UAV.mavlink._old_camera import CameraClient, CameraServer, MAVCom, boot_time_str
from UAV.mavlink.component import Component, mavutil, mavlink
from UAV.camera.gst_cam import CV2Camera, GSTCamera, read_camera_dict_from_toml
from gstreamer import  GstPipeline
import gstreamer.utils as gst_utils
import time
from pathlib import Path
import cv2

from UAV.utils import config_dir

MAV_TYPE_GCS = mavutil.mavlink.MAV_TYPE_GCS
MAV_TYPE_CAMERA = mavutil.mavlink.MAV_TYPE_CAMERA
# cli = GimbalClient(mav_connection=None, source_component=11, mav_type=MAV_TYPE_GCS, debug=False)
# gim1 = GimbalServer(mav_connection=None, source_component=22, mav_type=MAV_TYPE_CAMERA, debug=False)

con2 = "udpin:192.168.122.84:14445"
con2 = "udpin:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"

if __name__ == '__main__':
    print (f"boot_time_str = {boot_time_str = }")

    cam_gst_1 = GSTCamera(camera_dict=read_camera_dict_from_toml(config_dir() / "test_camera_0.toml"))

    with MAVCom(con2, source_system=222, debug=False) as server:

        server.add_component(CameraServer(mav_type=MAV_TYPE_CAMERA, source_component=22, camera=cam_gst_1, debug=False))
        while True:
            while cam_gst_1.capture_thread_is_alive:
                if cam_gst_1.last_image is not None:
                    cv2.imshow('gst_src', cam_gst_1.last_image)
                    cam_gst_1.last_image = None
                    cv2.waitKey(10)

                cv2.destroyAllWindows()

            time.sleep(0.01)

