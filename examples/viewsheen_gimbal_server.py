#!/usr/bin/env python
"""
viewsheen_sdk gimbal control
"""

import time
import numpy as np
from UAV import MAVCom
from UAV.mavlink import mavlink
from UAV.mavlink.vs_gimbal import GimbalServer

if __name__ == '__main__':


    con2 = "udpout:192.168.1.175:14445"
    # con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"

    with MAVCom(con2, source_system=222, ) as server:
        server.add_component(GimbalServer(mav_type=mavlink.MAV_TYPE_GIMBAL, source_component=mavlink.MAV_COMP_ID_GIMBAL, loglevel=10))
        time.sleep(0.1)

        while True:
            time.sleep(0.01 )
       
