"""
Request a message from a flight controller (e.g. PX4) using the MAV_CMD_REQUEST_MESSAGE command.
Here we request  MAVLINK_MSG_ID_RC_CHANNELS
"""

import asyncio
import random
import time

import pymavlink.dialects.v20.all as dialect

from UAV.cameras.gst_cam import GSTCamera
from UAV.logging import LogLevels
from UAV.mavlink import MAVCom, mavlink, CameraServer
from UAV.mavlink.client_component import ClientComponent
from UAV.utils import config_dir, get_platform, toml_load
from UAV.mavlink.message_request import MessageRequest

# assert os.environ['MAVLINK20'] == '1', "Set the environment variable before from pymavlink import mavutil  library is imported"
# from pymavlink import mavutil

# utils.set_gst_debug_level(Gst.DebugLevel)
# con1 = "udpin:localhost:14445"
# con1 = "/dev/ttyACM0" "/dev/ttyUSB1"
# con1, con2 = "/dev/ttyUSB0", "/dev/ttyUSB1"
# con1 = "udpout:192.168.122.84:14445"
# con1 = "udpin:10.42.0.1:14445"

mach = get_platform()
conf_path = config_dir()
config_dict = toml_load(conf_path / f"{mach}_server_config.toml")
mav_connection = config_dict['mavlink']['connection']

print(f"{mach = }, {conf_path = } {mav_connection = }")
print(config_dict)

# mav_connection = "/dev/ttyUSB1"
source_system = 255
target_system = 222

def on_message(msg: mavlink.MAVLink_message):
    # print(msg)
    if msg.get_type() in ['STATUSTEXT']:
        print(f"***** RC {msg}")

async def main():
    with MAVCom(mav_connection, source_system=config_dict['mavlink']['source_system'], loglevel=20) as UAV_server:
        UAV_server.on_message = on_message

        # mq = MessageRequest(UAV_server)
        # mq.log.info(f"{mq = }")
        server_config_dict = toml_load(config_dir() / f"test_server_config.toml")
        cam_0 = GSTCamera(server_config_dict, camera_dict=toml_load(config_dir() / "test_cam_0.toml"), loglevel=LogLevels.DEBUG)
        comp: CameraServer = UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_0, loglevel=20))
        ret = await comp.wait_heartbeat(target_system=1, target_component=1, timeout=5)  # from FC
        print(f"Heartbeat {ret = }")
        cam_snapping = False
        while True:
            msg = await comp.request_message(msg_id=mavlink.MAVLINK_MSG_ID_RC_CHANNELS, target_system=1, target_component=1)
            # print(f"request_message {msg}")
            if msg == mavlink.MAVLINK_MSG_ID_RC_CHANNELS:
                print(f"request_message {msg}")
                if msg.chancount == 0:
                    print("RC might not be connected")
            if msg is not None:
                # RC channel 7 switch is used to trigger the message
                print(f"{msg.chan7_raw = }  ", end='')
                print(f"RC_CHANNELS: chancount = {msg.chancount}: {msg.chan1_raw}, {msg.chan2_raw}, {msg.chan3_raw}, {msg.chan4_raw}, {msg.chan5_raw}, {msg.chan6_raw}, {msg.chan7_raw}, {msg.chan8_raw}, {msg.chan9_raw}, {msg.chan10_raw}, {msg.chan11_raw}, {msg.chan12_raw}, {msg.chan13_raw}, {msg.chan14_raw}, {msg.chan15_raw}, {msg.chan16_raw}, {msg.chan17_raw}, {msg.chan18_raw}")

                if msg.chan7_raw > 1200:
                    if not cam_snapping:
                        text = f"Camera taking snapshots: {msg.chan7_raw}"
                        # text = f"Roll a dice: {random.randint(1, 6)} flip a coin: {random.randint(0, 1)}"
                        comp.master.mav.statustext_send(mavlink.MAV_SEVERITY_INFO, text=text.encode("utf-8"))
                        print(f"Start Sent ")
                        comp.camera.image_start_capture(1, 0)

                    cam_snapping = True

                else:
                    if cam_snapping:
                        text = f"Camera stopped taking snapshots: {msg.chan7_raw}"
                        # text = f"Roll a dice: {random.randint(1, 6)} flip a coin: {random.randint(0, 1)}"
                        comp.master.mav.statustext_send(mavlink.MAV_SEVERITY_INFO, text=text.encode("utf-8"))
                        print(f"Stop Sent ")
                        comp.camera.image_stop_capture()
                    cam_snapping = False

                    # await comp.send_command(target_system=1, target_component=1, command_id=mavlink.MAV_CMD_DO_SET_MODE, params=[mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 0, 0, 0, 0, 0, 0])
                    # print(f"Sent {mavlink.MAV_CMD_DO_SET_MODE} {mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED}")
            time.sleep(0.01)



if __name__ == '__main__':
    print(__doc__)
    asyncio.run(main())
