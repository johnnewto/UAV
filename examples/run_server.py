import asyncio
import time

import cv2

from gstreamer import GstContext
from UAV.cameras.gst_cam import GSTCamera, logging
from UAV.logging import LogLevels
from mavcom.mavlink import MAVCom, mavlink
from UAV.mavlink import CameraServer
from UAV.mavlink.gimbal_server_viewsheen import GimbalServerViewsheen
from UAV.utils import config_dir, get_platform, boot_time_str, toml_load
# import platform
import subprocess

# from pathlib import Path

# print(platform.processor())

# cli = GimbalClient(mav_connection=None, source_component=11, mav_type=MAV_TYPE_GCS, debug=False)
# gim1 = GimbalServer(mav_connection=None, source_component=22, mav_type=MAV_TYPE_CAMERA, debug=False)

# con2 = "udpout:10.42.0.1:14445"
# con2 = "udpout:192.168.1.175:14445"
# con2 = "udpout:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"

# ENCODER = '265enc'
# ENCODER = ''

# def config_dir():
#     return Path(__file__).parent.parent / "config"
#
# con2 = "udpout:192.168.1.175:14445" if mach == 'jetson' else "udpout:localhost:14445"
# con2 = "/dev/ttyUSB0" if mach == 'jetson' else "/dev/ttyUSB1"


async def main():
    logging.info(f"boot_time_str = {boot_time_str = }")

    mach = get_platform()
    conf_path = config_dir()
    config_dict = toml_load(conf_path / f"{mach}_server_config.toml")
    mav_connection = config_dict['mavlink']['connection']

    print(f"{mach = }, {conf_path = } {mav_connection = }")
    print(config_dict)

    usb_mount_command = config_dict['usb_mount_command']
    subprocess.run(usb_mount_command.split())

    print("Starting GSTCameras")
    cam_0 = GSTCamera(config_dict, camera_dict=toml_load(conf_path / f"{mach}_cam_0.toml"), loglevel=LogLevels.INFO)
    cam_1 = GSTCamera(config_dict, camera_dict=toml_load(conf_path / f"{mach}_cam_1.toml"), loglevel=LogLevels.INFO)
    cam_2 = GSTCamera(config_dict, camera_dict=toml_load(conf_path / f"viewsheen.toml"), loglevel=LogLevels.INFO)

    print("*** Starting MAVcom")
    try:
        UAV_server = MAVCom(mav_connection, source_system=222, loglevel=LogLevels.DEBUG)
    except Exception as e:
        print(f"*** MAVCom failed to start: {e} **** ")
        cam_0.close()
        cam_1.close()
        cam_2.close()
        exit(1)

    with GstContext():
        with UAV_server:  # This normally runs on drone
            # UAV_server.add_component(CameraServer(mav_type=MAV_TYPE_CAMERA, source_component=22, camera=cam_gst_1))
            comp0: CameraServer = UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_0, loglevel=20))
            comp1: CameraServer = UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA2, camera=cam_1, loglevel=20))
            UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA3, camera=cam_2, loglevel=20))

            UAV_server.add_component(GimbalServerViewsheen(mav_type=mavlink.MAV_TYPE_GIMBAL, source_component=mavlink.MAV_COMP_ID_GIMBAL, loglevel=20))

            last_time = time.time()
            bitrate = 1000000

            # cam_0.image_start_capture(1,100)
            # cam_0.video_start_streaming()
            # cam_1.video_start_streaming()
            # cam_2.video_start_streaming()

            cam_snapping = False
            while True:
                msg = await comp0.request_message(msg_id=mavlink.MAVLINK_MSG_ID_RC_CHANNELS, target_system=1, target_component=1)
                # print(f"request_message {msg}")
                if msg == mavlink.MAVLINK_MSG_ID_RC_CHANNELS:
                    print(f"request_message {msg}")
                    if msg.chancount == 0:
                        print("RC might not be connected")
                if msg is not None:
                    # RC channel 7 switch is used to trigger the message
                    print(f"{msg.chan7_raw = }  ", end='')
                    print(
                        f"RC_CHANNELS: chancount = {msg.chancount}: {msg.chan1_raw}, {msg.chan2_raw}, {msg.chan3_raw}, {msg.chan4_raw}, {msg.chan5_raw}, {msg.chan6_raw}, {msg.chan7_raw}, {msg.chan8_raw}, {msg.chan9_raw}, {msg.chan10_raw}, {msg.chan11_raw}, {msg.chan12_raw}, {msg.chan13_raw}, {msg.chan14_raw}, {msg.chan15_raw}, {msg.chan16_raw}, {msg.chan17_raw}, {msg.chan18_raw}")

                    if msg.chan7_raw > 1200:
                        if not cam_snapping:
                            text = f"Camera taking snapshots: {msg.chan7_raw}"
                            # text = f"Roll a dice: {random.randint(1, 6)} flip a coin: {random.randint(0, 1)}"
                            comp0.master.mav.statustext_send(mavlink.MAV_SEVERITY_INFO, text=text.encode("utf-8"))
                            print(f"Start Sent ")
                            comp0.camera.image_start_capture(1, 0)
                            comp1.camera.image_start_capture(1, 0)

                        cam_snapping = True

                    else:
                        if cam_snapping:
                            text = f"Camera stopped taking snapshots: {msg.chan7_raw}"
                            # text = f"Roll a dice: {random.randint(1, 6)} flip a coin: {random.randint(0, 1)}"
                            comp0.master.mav.statustext_send(mavlink.MAV_SEVERITY_INFO, text=text.encode("utf-8"))
                            print(f"Stop Sent ")
                            comp0.camera.image_stop_capture()
                            comp1.camera.image_stop_capture()
                        cam_snapping = False

                        # await comp.send_command(target_system=1, target_component=1, command_id=mavlink.MAV_CMD_DO_SET_MODE, params=[mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 0, 0, 0, 0, 0, 0])
                        # print(f"Sent {mavlink.MAV_CMD_DO_SET_MODE} {mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED}")
                time.sleep(0.5)

    cv2.destroyAllWindows()
    time.sleep(0.01)
    cam_0.close()
    cam_1.close()
    cam_2.close()
if __name__ == '__main__':
    print(__doc__)
    asyncio.run(main())