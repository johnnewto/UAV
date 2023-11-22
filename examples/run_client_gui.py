import asyncio
import time

from UAV.manager import Gui
from UAV.mavlink import CameraClient, MAVCom, mavlink
from UAV.mavlink.gimbal_client import GimbalClient
from UAV.utils import helpers
from UAV.utils.general import boot_time_str

# con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB1"
# con1, con2 = "/dev/ttyUSB0", "/dev/ttyUSB1"
# con1 = "udpout:192.168.122.84:14445"
con1 = "udpin:localhost:14445"
# con1 = "udpin:10.42.0.1:14445"
# con1 = "udpin:192.168.1.175:14445"     # this is the wlan IP of this pc
# utils.set_gst_debug_level(Gst.DebugLevel)


async def main():
    with MAVCom(con1, source_system=111, ) as client:
        # with MAVCom(con2, source_system=222, ) as server:
        cam: CameraClient = client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=20))
        gimbal: GimbalClient = client.add_component(GimbalClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=12, loglevel=10))
        ret = await cam.wait_heartbeat(target_system=222, target_component=mavlink.MAV_COMP_ID_CAMERA, timeout=3)
        print(f"Heartbeat {ret = }")
        time.sleep(0.1)

        # Run the main function using asyncio.run
        gui = Gui(camera_client=cam, gimbal_client=gimbal)
        t1 = asyncio.create_task(gui.find_cameras())
        t3 = asyncio.create_task(gui.run_gui())
        t4 = asyncio.create_task(gui.gimbal_view())

        try:
            # await asyncio.gather(t1, t2, t3)
            # await asyncio.gather(t1, t3, )
            await asyncio.gather(t1, t3, t4)
        except asyncio.CancelledError:
            print("CancelledError")
            pass


if __name__ == '__main__':
    print(f"{boot_time_str =}")
    decoder = 'h264'
    print(f"Starting dispalays for {decoder = }")
    p = helpers.start_displays(display_type='cv2', decoder=decoder, num_cams=2, port=5000)
    # p = helpers.dotest()
    asyncio.run(main())
    p.terminate()
