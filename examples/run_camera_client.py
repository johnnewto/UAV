import asyncio
import time

from UAV.camera.gst_cam import GSTCamera
from UAV.mavlink import CameraClient, CameraServer, MAVCom, mavlink
from UAV.utils import helpers
from UAV.utils.general import boot_time_str, toml_load, config_dir

con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"


# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"
# con1 = "udpout:192.168.122.84:14445"
# con1 = "udpout:localhost:14445"


async def main():
    with MAVCom(con1, source_system=111, ) as client:
        with MAVCom(con2, source_system=222, ) as server:
            cam: CameraClient = client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11))
            # add UAV cameras, This normally runs on drone
            cam_1 = GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_0.toml"))
            cam_2 = GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_1.toml"))

            server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=22, camera=cam_1))
            server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=23, camera=cam_2))

            ret = await cam.wait_heartbeat(target_system=222, target_component=22, timeout=1)
            print(f"Heartbeat {ret = }")
            time.sleep(0.1)
            cam.set_target(222, 22)

            await cam.video_start_streaming(222, 22, )
            time.sleep(2)
            await cam.video_stop_streaming(222, 22, )
            await cam.video_start_streaming(222, 23, )
            time.sleep(2)
            await cam.video_stop_streaming(222, 23, )


if __name__ == '__main__':
    print(f"{boot_time_str =}")
    p = helpers.start_displays(num_cams=2, port=5000)
    # p = helpers.dotest()
    asyncio.run(main())
    p.terminate()
