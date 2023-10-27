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
    with MAVCom(con1, source_system=111, loglevel=20) as client:
        with MAVCom(con2, source_system=222, loglevel=20) as server:
            gcs: CameraClient = client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=20))
            # add UAV cameras, This normally runs on drone

            cam_front = AirsimCamera(camera_name='front', camera_dict=toml_load(config_dir() / "airsim_cam_front.toml"), loglevel=20)
            cam_left = AirsimCamera(camera_name='left', camera_dict=toml_load(config_dir() / "airsim_cam_left.toml"))
            cam_right = AirsimCamera(camera_name='right', camera_dict=toml_load(config_dir() / "airsim_cam_right.toml"))
            cam_down = AirsimCamera(camera_name='down', camera_dict=toml_load(config_dir() / "airsim_cam_down.toml"))
            server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_left))
            server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA2, camera=cam_front))
            server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA3, camera=cam_right))
            server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA4, camera=cam_down))

            ret = await gcs.wait_heartbeat(target_system=222, target_component=22, timeout=1)
            cmd = DroneCommands(takeoff_z=-20)

            print(f"Heartbeat {ret = }")

            gui = Gui(client=gcs, auto=cmd.start, reset=cmd.reset_position, pause=cmd.cancel_last_task)

            t1 = asyncio.create_task(gui.find_cameras())
            t2 = asyncio.create_task(gui.run_gui())

            try:
                await asyncio.gather(t1, t2)
            except asyncio.CancelledError:
                print("CancelledError")
                pass
            cmd.stop()
            # time.sleep(0)
            cmd.disarm()
            cmd.close()


if __name__ == '__main__':
    p = helpers.start_displays(display_type='cv2', num_cams=4, port=5000)
    asyncio.run(main())
    p.terminate()
