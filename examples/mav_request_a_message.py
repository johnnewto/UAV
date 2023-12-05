"""
Request a message from a flight controller (e.g. PX4) using the MAV_CMD_REQUEST_MESSAGE command.
Here we request  MAVLINK_MSG_ID_RC_CHANNELS
"""

import asyncio
import os
import time
# assert os.environ['MAVLINK20'] == '1', "Set the environment variable before from pymavlink import mavutil  library is imported"
# from pymavlink import mavutil

from UAV.mavlink import MAVCom
from UAV.mavlink import CameraClient, MAVCom, mavlink, mavutil
from UAV.mavlink.client_component import ClientComponent
import random
import pymavlink.dialects.v20.all as dialect

# utils.set_gst_debug_level(Gst.DebugLevel)
# con1 = "udpin:localhost:14445"
# con1 = "/dev/ttyACM0" "/dev/ttyUSB1"
# con1, con2 = "/dev/ttyUSB0", "/dev/ttyUSB1"
# con1 = "udpout:192.168.122.84:14445"
# con1 = "udpin:10.42.0.1:14445"

mav_connection = "/dev/ttyUSB1"
source_system = 255
target_system = 222


async def main():
    with MAVCom(mav_connection, source_system=source_system, loglevel=20) as client:
        comp = client.add_component(ClientComponent(mav_type=mavlink.MAV_TYPE_GCS, source_component=1, loglevel=20))  # MAV_TYPE_GCS
        ret = await comp.wait_heartbeat(target_system=1, target_component=1, timeout=5)
        print(f"Heartbeat {ret = }")

        # ret = await comp.request_message(msg_id=mavlink.MAVLINK_MSG_ID_RC_CHANNELS, target_system=1, target_component=1)
        # print(f"request_message {ret}")
        # if ret == mavlink.MAVLINK_MSG_ID_RC_CHANNELS:
        #     print(f"request_messages {ret}")
        #     if ret.chancount == 0:
        #         print("RC might not be connected")
        # # this will stream all messages to the channel
        # # client.master.mav.request_data_stream_send(1, 1,
        # #                                            mavutil.mavlink.MAV_DATA_STREAM_ALL,
        # #                                            1, 1)

        while True:
            msg = await comp.request_message(msg_id=mavlink.MAVLINK_MSG_ID_RC_CHANNELS, target_system=1, target_component=1)
            # print(f"request_message {msg}")
            if msg == mavlink.MAVLINK_MSG_ID_RC_CHANNELS:
                print(f"request_message {msg}")
                if msg.chancount == 0:
                    print("RC might not be connected")
            if msg is not None:
                print(f"{msg.chan7_raw = }  ", end='')
                print(f"RC_CHANNELS: chancount = {msg.chancount}: {msg.chan1_raw}, {msg.chan2_raw}, {msg.chan3_raw}, {msg.chan4_raw}, {msg.chan5_raw}, {msg.chan6_raw}, {msg.chan7_raw}, {msg.chan8_raw}, {msg.chan9_raw}, {msg.chan10_raw}, {msg.chan11_raw}, {msg.chan12_raw}, {msg.chan13_raw}, {msg.chan14_raw}, {msg.chan15_raw}, {msg.chan16_raw}, {msg.chan17_raw}, {msg.chan18_raw}")

                if msg.chan7_raw > 1200:
                    # msg = mavlink.MAVLink_statustext_message(mavlink.MAV_SEVERITY_WARNING, b"Hello")
                    # comp.send_message(msg)
                    text = f"Roll a dice: {random.randint(1, 6)} flip a coin: {random.randint(0, 1)}"

                    # create STATUSTEXT message
                    message = dialect.MAVLink_statustext_message(severity=dialect.MAV_SEVERITY_INFO,
                                                                 text=text.encode("utf-8"))

                    # send message to the GCS
                    comp.master.mav.send(message)
                    # comp.master.mav.statustext_send(mavlink.MAV_SEVERITY_WARNING, b"Hello")
                    print(f"Sent ")
                    time.sleep(1)
                    # await comp.send_command(target_system=1, target_component=1, command_id=mavlink.MAV_CMD_DO_SET_MODE, params=[mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 0, 0, 0, 0, 0, 0])
                    # print(f"Sent {mavlink.MAV_CMD_DO_SET_MODE} {mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED}")
            time.sleep(0.1)


if __name__ == '__main__':
    print(__doc__)
    asyncio.run(main())
