import asyncio
import time

from UAV.airsim.commands import DroneCommands
from UAV.cameras.airsim_cam import AirsimCamera
from UAV.gimbals.airsim_gimbal import AirsimGimbal
from UAV.logging import LogLevels
from UAV.manager import Gui
from UAV.mavlink import CameraClient, CameraServer, MAVCom, mavlink, GimbalServer, GimbalManagerClient
from UAV.utils import helpers
from UAV.utils.general import toml_load, config_dir

# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB1"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyACM2"
async def main():
    with (MAVCom(con1, source_system=111, loglevel=20) as gcs_mavlink):  # ground control station mavlink

        with MAVCom(con2, source_system=222, loglevel=20) as drone_mavlink:  # drone mavlink

            # connect to the cameras manager
            gcs_cam_manager = gcs_mavlink.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=20))
            gcs_gim: GimbalManagerClient = gcs_mavlink.add_component(GimbalManagerClient(mav_type=mavlink.MAV_TYPE_GIMBAL, source_component=12, loglevel=LogLevels.INFO))
            server_config_dict = toml_load(config_dir() / f"test_server_config.toml")

            # start cameras, This would run on a drone companion computer
            cam_front = AirsimCamera(server_config_dict, camera_dict=toml_load(config_dir() / "airsim_cam_center.toml"))
            cam_left = AirsimCamera(server_config_dict, camera_dict=toml_load(config_dir() / "airsim_cam_left.toml"))
            cam_right = AirsimCamera(server_config_dict, camera_dict=toml_load(config_dir() / "airsim_cam_right.toml"))
            cam_down = AirsimCamera(server_config_dict, camera_dict=toml_load(config_dir() / "airsim_cam_down.toml"))
            gim_1 = AirsimGimbal(camera_name='center', loglevel=10)

            # connect cameras to mavlink
            drone_mavlink.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_left))
            drone_mavlink.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA2, camera=cam_front))
            drone_mavlink.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA3, camera=cam_right))
            drone_mavlink.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA4, camera=cam_down))
            drone_mavlink.add_component(GimbalServer(mav_type=mavlink.MAV_TYPE_GIMBAL, source_component=mavlink.MAV_COMP_ID_GIMBAL, gimbal=gim_1, loglevel=20))

            # # wait for heartbeat signal from the drone
            # ret = await gcs_cam_manager.wait_heartbeat(remote_mav_type=mavlink.MAV_TYPE_CAMERA, timeout=2)
            # print(f"Camera Heartbeat {ret = }")
            ret = await gcs_gim.wait_heartbeat(remote_mav_type=mavlink.MAV_TYPE_GIMBAL, timeout=2)
            print(f"GIMBAL Heartbeat {ret = }")

            # Start the Airsim "basic Autopilot"
            cmd = DroneCommands(takeoff_z=-35)

            asc = cam_front.asc   # asc = AirsimClient

            # asc.set_camera_orientation(camera_name='down', roll=40, pitch=0, yaw=0)
            # await gcs_gim.cmd_pitch_yaw(40, 0, 0, 0, 0, 0, 222, mavlink.MAV_COMP_ID_GIMBAL)

            # place objects in the simulator

            # cam_front.asc.confirmConnection()
            # print("Placing objects")
            #
            # asc.place_object("Sofa_02", 0.0, -50.0, -35.0, scale=0.5)
            # asc.place_object("Sofa_02", 0.0, -70.0, -36.0, scale=0.5)
            # asc.place_object("Sofa_02", 20.0, -50.0, -35.0, scale=0.5)
            # asc.place_object("Sofa_02", -20.0, -50.0, -36.0, scale=0.5)

            # Run the cameras manager GUI (using asyncio.run)
            gui = Gui(camera_client=gcs_cam_manager, gimbal_client=gcs_gim,  auto=cmd.start, reset=cmd.reset_position, pause=cmd.cancel_last_task)
            t1 = asyncio.create_task(gui.find_cameras())
            t2 = asyncio.create_task(gui.find_gimbals())
            t3 = asyncio.create_task(gui.run_gui())

            # wait for the GUI to finish
            try:
                await asyncio.gather(t1, t2, t3)
            except asyncio.CancelledError:
                print("CancelledError")

            # shutdown
            cmd.reset_position(), cmd.stop(), cmd.disarm(), cmd.close()
            cam_front.close()
            # cam_left.close(), cam_right.close(), cam_down.close()


if __name__ == '__main__':
    # p = helpers.start_displays(display_type='cv2')
    client_config_dict = toml_load(config_dir() / f"client_airsim_config.toml")
    p = helpers.start_displays(client_config_dict, display_type='cv2')
    # p = helpers.start_displays(display_type='cv2', num_cams=4, names=['front'], port=5000)
    asyncio.run(main())
    p.terminate()
