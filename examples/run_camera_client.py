import asyncio
import time
import platform
from UAV.mavlink import CameraClient, MAVCom, mavlink
from UAV.utils import helpers
from UAV.utils.general import boot_time_str, toml_load, config_dir
# con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB1"
# con1, con2 = "/dev/ttyUSB0", "/dev/ttyUSB1"
# con1 = "udpout:192.168.122.84:14445"
con1 = "udpin:localhost:14445"
# con1 = "udpin:192.168.144.1:14445"

async def main():
    with MAVCom(con1, source_system=111, ) as client:
        # with MAVCom(con2, source_system=222, ) as server:
        cam: CameraClient = client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=20))
        ret = await cam.wait_heartbeat(target_system=222, target_component=mavlink.MAV_COMP_ID_CAMERA, timeout=3)
        print(f"Heartbeat {ret = }")
        time.sleep(0.1)
        cam.set_target(222, mavlink.MAV_COMP_ID_CAMERA)
        for i in range(5):
            await cam.video_start_streaming(222, mavlink.MAV_COMP_ID_CAMERA, )
            time.sleep(2)
            await cam.video_stop_streaming(222, mavlink.MAV_COMP_ID_CAMERA, )
            time.sleep(2)
        # await cam.video_start_streaming(222, 23, )
        # time.sleep(2)
        # await cam.video_stop_streaming(222, 23, )
        await cam.video_start_streaming(222, mavlink.MAV_COMP_ID_CAMERA, )
        time.sleep(2)


if __name__ == '__main__':
    print(f"{boot_time_str =}")
    # p = helpers.start_displays(num_cams=2, port=5000)
    client_config_dict = toml_load(config_dir() / f"client_config.toml")
    print(client_config_dict)
    if platform.processor() != 'aarch64':
        client_config_dict['camera_udp_decoder'] = 'h264'  # on pc override as h264
    p = helpers.start_displays(client_config_dict, display_type='cv2')
    # p = helpers.dotest()
    asyncio.run(main())
    p.terminate()
