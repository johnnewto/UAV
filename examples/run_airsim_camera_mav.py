import asyncio
import time

from UAV.airsim.commands import DroneCommands
from UAV.camera.airsim_cam import AirsimCamera
from UAV.manager import Gui
from UAV.mavlink import CameraClient, CameraServer, MAVCom, mavlink
from UAV.utils import helpers
from UAV.utils.general import toml_load, config_dir

# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"


async def main():
    with MAVCom(con1, source_system=111, loglevel=20) as gcs_mavlink:  # ground control station mavlink
        with MAVCom(con2, source_system=222, loglevel=20) as drone_mavlink:  # drone mavlink

            # connect to the camera manager
            gcs_cam_manager = gcs_mavlink.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=20))

            # start cameras, This would run on a drone companion computer
            cam_front = AirsimCamera(camera_name='center', camera_dict=toml_load(config_dir() / "airsim_cam_front.toml"))
            cam_left = AirsimCamera(camera_name='left', camera_dict=toml_load(config_dir() / "airsim_cam_left.toml"))
            cam_right = AirsimCamera(camera_name='right', camera_dict=toml_load(config_dir() / "airsim_cam_right.toml"))
            cam_down = AirsimCamera(camera_name='down', camera_dict=toml_load(config_dir() / "airsim_cam_down.toml"))

            # place objects in the simulator
            cam_front.asc.place_object("Sofa_02", 50.0, 20.0, -25.0, scale=0.5)
            cam_front.asc.place_object("Sofa_02", 50.0, -20.0, -25.0, scale=0.5)
            cam_front.asc.place_object("Sofa_02", 55.0, -0.0, -21.0, scale=0.5)

            # connect cameras to mavlink
            drone_mavlink.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_left))
            drone_mavlink.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA2, camera=cam_front))
            drone_mavlink.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA3, camera=cam_right))
            drone_mavlink.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA4, camera=cam_down))

            # wait for heartbeat signal from the drone
            ret = await gcs_cam_manager.wait_heartbeat(target_system=222, target_component=22, timeout=1)
            print(f"Heartbeat {ret = }")
            # time.sleep(5)
            # Start the Airsim "basic Autopilot"
            cmd = DroneCommands(takeoff_z=-20)

            # Run the camera manager GUI (using asyncio.run)
            gui = Gui(client=gcs_cam_manager, auto=cmd.start, reset=cmd.reset_position, pause=cmd.cancel_last_task)
            t1 = asyncio.create_task(gui.find_cameras())
            t2 = asyncio.create_task(gui.run_gui())

            # wait for the GUI to finish
            # await asyncio.gather(t1, t2)
            try:
                await asyncio.gather(t1, t2)
            except asyncio.CancelledError:
                print("CancelledError")

            # shutdown
            cmd.reset_position(), cmd.stop(), cmd.disarm(), cmd.close()
            print("Closing cameras")
            cam_front.close(), cam_left.close(), cam_right.close(), cam_down.close()



if __name__ == '__main__':
    p = helpers.start_displays(display_type='cv2', num_cams=4, names=['front', 'left', 'right', 'down'], port=5000)
    asyncio.run(main())
    p.terminate()
