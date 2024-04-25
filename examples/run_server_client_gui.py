
""" This is an example of how to run a server and client with a GUI"""

import asyncio
import platform

from gstreamer import GstContext

from UAV.cameras.gst_cam import GSTCamera
from UAV.logging import LogLevels
from UAV.manager import Gui
from UAV.mavlink import CameraClient, CameraServer, MAVCom, mavlink, GimbalServerViewsheen
from UAV.mavlink.gimbal_client import GimbalClient
from UAV.utils import helpers
from UAV.utils.general import boot_time_str, toml_load, config_dir
import  plugins
from gstreamer import CallbackHandler

# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)


async def main():
    con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
    # con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB1"
    # con1, con2 = "/dev/ttyACM0", "/dev/ttyACM2"
    # logger.disabled = True
    print(f"{boot_time_str =}")

    plugins.Base.plugins_dict['BallTracker']().start()  # This is how you can start a plugin


    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread
    # if True:
        with MAVCom(con1, source_system=111, loglevel=LogLevels.CRITICAL) as GCS_client:  # This normally runs on GCS
            with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server:  # This normally runs on drone

                # add GCS manager
                gcs: CameraClient = GCS_client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=LogLevels.INFO))
                gimbal: GimbalClient = GCS_client.add_component(GimbalClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=12, loglevel=LogLevels.INFO))

                server_config_dict = toml_load(config_dir() / f"test_server_config.toml")
                print(server_config_dict)
                # add UAV cameras, This normally runs on drone
                cam_0 = GSTCamera(server_config_dict, camera_dict=toml_load(config_dir() / "test_cam_0.toml"), loglevel=LogLevels.DEBUG)
                cam_1 = GSTCamera(server_config_dict, camera_dict=toml_load(config_dir() / "test_cam_1.toml"), loglevel=LogLevels.DEBUG)
                # cam_2 = GSTCamera(server_config_dict, camera_dict=toml_load(config_dir() / f"viewsheen_H264.toml"), loglevel=LogLevels.INFO) # viewsheen camera

                # this is an examle of how to set a plugin as a callback handler
                cam_0.tracking_handler = CallbackHandler(callback=plugins.Base.plugins_dict['BallTracker']().on_buffer, id=0, name='cam_0')

                UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_0, loglevel=LogLevels.INFO))
                UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA2, camera=cam_1, loglevel=LogLevels.INFO))
                # UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA3, camera=cam_2, loglevel=LogLevels.INFO))
                # UAV_server.add_component(GimbalServerViewsheen(mav_type=mavlink.MAV_TYPE_GIMBAL, source_component=mavlink.MAV_COMP_ID_GIMBAL, loglevel=LogLevels.INFO))

                ret = await gcs.wait_heartbeat(remote_mav_type=mavlink.MAV_TYPE_CAMERA, timeout=2)
                print(f"Camera Heartbeat {ret = }")

                gui = Gui(camera_client=gcs, gimbal_client=gimbal)
                t1 = asyncio.create_task(gui.find_cameras())
                t3 = asyncio.create_task(gui.run_gui())
                # t4 = asyncio.create_task(gui.gimbal_control())

                try:
                    # await asyncio.gather(t1, t3, t4)
                    await asyncio.gather(t1, t3)
                except asyncio.CancelledError:
                    print("CancelledError")
                    pass

                cam_0.close()
                # cam_1.close()
                # cam_2.close()


if __name__ == '__main__':

    client_config_dict = toml_load(config_dir() / f"client_config.toml")
    print(client_config_dict)
    if platform.processor() != 'aarch64':
        client_config_dict['camera_udp_decoder'] = 'h264'  # on pc override as h264

    client_config_dict['camera_names'] = ['cam_0', 'cam_1'] # override names to 2 cameras
    client_config_dict['camera_ip_ports'] = [5000, 5001] # override ports to 2 cameras
    p = helpers.start_displays(client_config_dict, display_type='cv2')  # Todo show how this starts multiple displays
    asyncio.run(main())
    p.terminate()
