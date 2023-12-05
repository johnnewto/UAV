# import time

# from UAV.mavlink import MAVCom

# # utils.set_gst_debug_level(Gst.DebugLevel)
# # con1 = "udpin:localhost:14445"
# # con1 = "/dev/ttyACM0" "/dev/ttyUSB1"
# # con1, con2 = "/dev/ttyUSB0", "/dev/ttyUSB1"
# # con1 = "udpout:192.168.122.84:14445"
# # con1 = "udpin:10.42.0.1:14445"

# mav_connection = "/dev/ttyUSB0"
# source_system = 111
# target_system = 222

# with MAVCom(mav_connection, source_system=source_system, loglevel=10) as client:
#     while True:
#         time.sleep(0.1)
import asyncio
import os
import time
# assert os.environ['MAVLINK20'] == '1', "Set the environment variable before from pymavlink import mavutil  library is imported"
# from pymavlink import mavutil

from UAV.mavlink import MAVCom
from UAV.mavlink import CameraClient, MAVCom, mavlink, mavutil
from UAV.mavlink.client_component import ClientComponent


mav_connection = "/dev/ttyUSB0"
source_system = 255
target_system = 222


async def main():
    with MAVCom(mav_connection, source_system=source_system, loglevel=10) as client:
        comp = client.add_component(ClientComponent(mav_type=mavlink.MAV_TYPE_GCS, source_component=1, loglevel=10))  # MAV_TYPE_GCS
        ret = await comp.wait_heartbeat(target_system=1, target_component=1, timeout=5)
        print(f"Heartbeat {ret = }")
        client.master.mav.request_data_stream_send(1, 1,
                                                   mavutil.mavlink.MAV_DATA_STREAM_ALL,
                                                   1, 1)
        time.sleep(0.1)
        while True:
            time.sleep(0.1)


if __name__ == '__main__':
    asyncio.run(main())