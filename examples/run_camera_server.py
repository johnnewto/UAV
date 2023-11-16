import time

import cv2

from UAV.cameras.gst_cam import GSTCamera
from UAV.logging import LogLevels
from UAV.mavlink import CameraServer, MAVCom, mavlink
from UAV.utils import config_dir, boot_time_str, toml_load

# cli = GimbalClient(mav_connection=None, source_component=11, mav_type=MAV_TYPE_GCS, debug=False)
# gim1 = GimbalServer(mav_connection=None, source_component=22, mav_type=MAV_TYPE_CAMERA, debug=False)

con2 = "udpout:10.42.0.1:14445"
# con2 = "udpout:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"



if __name__ == '__main__':
    print (f"boot_time_str = {boot_time_str = }")
    cam_0 = GSTCamera(camera_dict=toml_load(config_dir() / "jetson_camera_0.toml"), loglevel=LogLevels.INFO)    
    cam_1 = GSTCamera(camera_dict=toml_load(config_dir() / "jetson_camera_1.toml"), loglevel=LogLevels.INFO)

    # with MAVCom(con2, source_system=222) as server:
    with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server:  # This normally runs on drone
        # UAV_server.add_component(CameraServer(mav_type=MAV_TYPE_CAMERA, source_component=22, camera=cam_gst_1))
        UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_0, loglevel=10))
        UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA2, camera=cam_1, loglevel=10))

        while cam_1.pipeline:
            if cam_1.last_image is not None:
                pass
                # cv2.imshow('gst_src', cam_1.last_image)
                # cam_1.last_image = None
                # cv2.waitKey(10)
            time.sleep(0.01)

    cv2.destroyAllWindows()
    time.sleep(0.01)

