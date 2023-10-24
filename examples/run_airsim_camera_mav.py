import asyncio
import time

from UAV.camera.airsim_cam import AirsimCamera
from UAV.manager import Gui
from UAV.mavlink import CameraClient, CameraServer, MAVCom, mavlink
from UAV.utils import helpers
from UAV.utils.general import toml_load, config_dir

# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"


async def main():
    with MAVCom(con1, source_system=111, loglevel=20) as client:
        with MAVCom(con2, source_system=222,  loglevel=20) as server:
            gcs: CameraClient = client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=20))
            # add UAV cameras, This normally runs on drone

            cam_1 = AirsimCamera(camera_name='front', camera_dict=toml_load(config_dir() / "airsim_cam_0.toml"), loglevel=20)
            cam_2 = AirsimCamera(camera_name='left', camera_dict=toml_load(config_dir() / "airsim_cam_1.toml"))

            server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=22, camera=cam_1))
            server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=23, camera=cam_2))

            ret = await gcs.wait_heartbeat(target_system=222, target_component=22, timeout=1)
            print(f"Heartbeat {ret = }")
            for i in range (5):
                await gcs.video_start_streaming(222, 22, )
                time.sleep(2)
                await gcs.video_stop_streaming(222, 22, )
                time.sleep(2)
                #
                # await gcs.video_start_streaming(222, 23, )
                # time.sleep(2)
                # await gcs.video_stop_streaming(222, 23, )

            gui = Gui(client=gcs)

            t1 = asyncio.create_task(gui.find_cameras())
            t2 = asyncio.create_task(gui.run_gui())

            try:
                await asyncio.gather(t1, t2)
            except asyncio.CancelledError:
                print("CancelledError")
                pass


if __name__ == '__main__':
    p = helpers.start_displays(num_cams=2, port=5000)
    asyncio.run(main())
    p.terminate()

