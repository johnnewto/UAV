#!/usr/bin/env python
"""
viewsheen_sdk gimbal control
"""

import time
import numpy as np
from UAV import MAVCom
from UAV.cameras.gst_cam import GSTCamera
from UAV.mavlink import mavlink, CameraServer
from UAV.mavlink.gimbal_server_viewsheen import GimbalServerViewsheen
from UAV.utils import toml_load, config_dir
from gstreamer import LogLevels

if __name__ == '__main__':


    con2 = "udpout:192.168.1.175:14445"
    con2 = "udpout:localhost:14445"
    # con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"
    cam_0 = GSTCamera(camera_dict=toml_load(config_dir() / f"test_viewsheen.toml"), loglevel=LogLevels.INFO)

    with MAVCom(con2, source_system=222, ) as server:
        server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_0, loglevel=LogLevels.INFO))
        server.add_component(GimbalServerViewsheen(mav_type=mavlink.MAV_TYPE_GIMBAL, source_component=mavlink.MAV_COMP_ID_GIMBAL, loglevel=LogLevels.INFO))
        time.sleep(0.1)

        while True:
            time.sleep(0.01)
       
