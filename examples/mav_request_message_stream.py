"""
Request messages from a flight controller (e.g. PX4) using the MAV_CMD_SET_MESSAGE_INTERVAL command.
Here we request  MAVLINK_MSG_ID_RC_CHANNELS at 1 second interval
"""

import asyncio
import time

from UAV.mavlink import Component, MAVCom, mavlink

# assert os.environ['MAVLINK20'] == '1', "Set the environment variable before from pymavlink import mavutil  library is imported"
# from pymavlink import mavutil

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
    with MAVCom(mav_connection, source_system=source_system, loglevel=10) as client:
        comp = client.add_component(Component(mav_type=mavlink.MAV_TYPE_GCS, source_component=1, loglevel=20))  # MAV_TYPE_GCS
        ret = await comp.wait_heartbeat(target_system=1, target_component=1, timeout=5)
        print(f"Heartbeat {ret = }")
        ret = await comp.request_message_stream(1, 1,
                                                msg_id=mavlink.MAVLINK_MSG_ID_RC_CHANNELS,
                                                interval=1000000)
        print(f"request_messages {ret}")
        if ret == mavlink.MAVLINK_MSG_ID_RC_CHANNELS:
            print(f"request_messages {ret}")
            if ret.chancount == 0:
                print("RC might not be connected")
        # this will stream all messages to the channel
        # client.master.mav.request_data_stream_send(1, 1,
        #                                            mavutil.mavlink.MAV_DATA_STREAM_ALL,
        #                                            1, 1)

        time.sleep(0.1)
        cond = comp.set_message_callback_cond(mavlink.MAVLINK_MSG_ID_RC_CHANNELS, 1, 1)
        while True:
            ret = await comp.wait_message_callback(cond, 1, remove_after=False)
            # if ret:
            msg = cond['msg']
            if msg is not None:
                print(f"RC_CHANNELS: chancount = {msg.chancount}: {msg.chan1_raw}, {msg.chan2_raw}, {msg.chan3_raw}, {msg.chan4_raw}, {msg.chan5_raw}, {msg.chan6_raw}, {msg.chan7_raw}, {msg.chan8_raw}, {msg.chan9_raw}, {msg.chan10_raw}, {msg.chan11_raw}, {msg.chan12_raw}, {msg.chan13_raw}, {msg.chan14_raw}, {msg.chan15_raw}, {msg.chan16_raw}, {msg.chan17_raw}, {msg.chan18_raw}")

            time.sleep(0.1)


if __name__ == '__main__':
    print(__doc__)
    asyncio.run(main())
