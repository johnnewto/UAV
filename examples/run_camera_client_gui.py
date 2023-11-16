import asyncio
import time

from UAV.mavlink import CameraClient, MAVCom, mavlink
from UAV.utils import helpers
from UAV.utils.general import boot_time_str
from UAV.manager import Gui

# con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB1"
# con1, con2 = "/dev/ttyUSB0", "/dev/ttyUSB1"
# con1 = "udpout:192.168.122.84:14445"
con1 = "udpin:localhost:14445"
con1 = "udpin:10.42.0.1:14445"

async def main():
    with MAVCom(con1, source_system=111, ) as client:
        # with MAVCom(con2, source_system=222, ) as server:
        cam: CameraClient = client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=20))
        ret = await cam.wait_heartbeat(target_system=222, target_component=mavlink.MAV_COMP_ID_CAMERA, timeout=3)
        print(f"Heartbeat {ret = }")
        time.sleep(0.1)

        # Run the main function using asyncio.run
        gui = Gui(camera_client=cam)
        t1 = asyncio.create_task(gui.find_cameras())
        # t2 = asyncio.create_task(gui.find_gimbals())
        t3 = asyncio.create_task(gui.run_gui())

        try:
            # await asyncio.gather(t1, t2, t3)
            await asyncio.gather(t1, t3)
        except asyncio.CancelledError:
            print("CancelledError")
            pass




if __name__ == '__main__':
    print(f"{boot_time_str =}")
    p = helpers.start_displays(display_type='cv2', num_cams=2, port=5000)
    # p = helpers.dotest()
    asyncio.run(main())
    p.terminate()
