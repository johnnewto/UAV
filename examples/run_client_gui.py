import argparse
import asyncio
import time

from UAV.manager import Gui
from UAV.mavlink import CameraClient, MAVCom, mavlink
from UAV.mavlink.gimbal_client import GimbalClient
from UAV.utils import config_dir, toml_load
from UAV.utils import helpers
from UAV.utils.general import boot_time_str


# utils.set_gst_debug_level(Gst.DebugLevel)
# con1 = "udpin:localhost:14445"
# con1 = "/dev/ttyACM0" "/dev/ttyUSB1"
# con1, con2 = "/dev/ttyUSB0", "/dev/ttyUSB1"
# con1 = "udpout:192.168.122.84:14445"
# con1 = "udpin:10.42.0.1:14445"


async def main(config_dict):
    try:
        client = MAVCom(config_dict['mavlink']['connection'], source_system=config_dict['mavlink']['source_system'], loglevel=10)
    except Exception as e:
        print(f"*** MAVCom failed to start: {e} **** ")
        return

    with client:
        # with MAVCom(con2, source_system=222, ) as server:
        cam: CameraClient = client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=config_dict['camera_component'], loglevel=20)) # MAV_TYPE_GCS
        gimbal: GimbalClient = client.add_component(GimbalClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=config_dict['gimbal_component'], loglevel=20))
        ret = await cam.wait_heartbeat(target_system=config_dict['mavlink']['target_system'], target_component=mavlink.MAV_COMP_ID_CAMERA, timeout=3)
        print(f"Heartbeat {ret = }")
        time.sleep(0.1)

        # Run the main function using asyncio.run
        gui = Gui(camera_client=cam, gimbal_client=gimbal)
        t1 = asyncio.create_task(gui.find_cameras())
        t3 = asyncio.create_task(gui.run_gui())
        # t4 = asyncio.create_task(gui.gimbal_view())

        try:

            await asyncio.gather(t1, t3)
        except asyncio.CancelledError:
            print("CancelledError")
            pass


if __name__ == '__main__':
    # get command line args
    parser = argparse.ArgumentParser(description='UAV camera GUI')
    parser.add_argument('-cl', '--connect_local', action='store_true', help='Connect to local camera server')
    args = parser.parse_args()

    config_dict = toml_load(config_dir() / f"client_config.toml")

    if args.connect_local:
        print("overwrite config_dict['mav_connection'] with local connection")
        config_dict['mav_connection'] = "udpin:localhost:14445"
        config_dict['camera_udp_decoder'] = 'h264'

    print(config_dict)

    print(f"{boot_time_str =}")

    p = helpers.start_displays(config_dict, display_type='cv2')
    # p = helpers.dotest()
    asyncio.run(main(config_dict))
    p.terminate()
