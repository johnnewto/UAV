import asyncio
import threading
from pathlib import Path

from UAV.airsim.commands import DroneCommands
from UAV.airsim.client import AirSimClient
from UAV.utils import config_dir

from UAV.utils.sim_linux import RunSim
from UAV.utils.display import puttext, VideoWriter, ScrollingLog, ScrollingLogHandler
from imutils import resize
import cv2
import logging
import time
# logging.basicConfig(format=
#                     '%(asctime)-8s,%(msecs)-3d %(levelname)5s [%(filename)10s:%(lineno)3d] %(message)s',
#                     datefmt='%H:%M:%S',
#                     level=logging.INFO)
import UAV.params as params

logger = logging.getLogger(params.LOGGING_NAME)  # Todo add this to params
logger.setLevel(params.LOGGING_LEVEL)
# log = ScrollingLog(bg_color=(0,0,0))
log = ScrollingLog(position=(20, 80), font_scale=1.5, color=(0, 0, 255), thickness=1)
handler_log = ScrollingLogHandler(log, logger)
logger.info(f"Hello World...")


async def main():
    asc = AirSimClient()
    # cmd = DroneCommands()
    # t = threading.Thread(target=cmd.do_tasklist, daemon=True)  # tasklist is a generator that returns tasks = [self.arm, self.takeoff, self.do_NH_path, self.rth, self.land, self.disarm]
    # t.start()

    framecounter = 1
    cam_num = 0
    cams = ["high_res", "front_center", "front_right", "front_left", "bottom_center", "back_center"]

    while (True):
        framecounter += 1
        state = asc.getMultirotorState()
        pos = state.kinematics_estimated.position
        img = asc.get_image(cams[cam_num], rgb2bgr=False)
        puttext(img, f"Frame: {framecounter} Pos: {pos.x_val:.2f}, {pos.y_val:.2f}, {pos.z_val:.2f}")

        img = resize(img, width=800)
        # log.update(f"Frame: {framecounter} Pos: {pos.x_val:.2f}, {pos.y_val:.2f}, {pos.z_val:.2f}")
        if framecounter % 100 == 0:
            print(f"Frame: {framecounter} Pos: {pos.x_val:.2f}, {pos.y_val:.2f}, {pos.z_val:.2f}")
        log.draw(img)
        cv2.imshow("Camera", img)

        k = cv2.waitKey(10)

        if k == ord('c') or k == ord('C'):
            cam_num += 1
            if cam_num >= len(cams):
                cam_num = 0
            # log.update(f"Camera: {cams[cam_num]}")
            logger.info(f"Camera: {cams[cam_num]}")

        if k == 27:
            # cmd.stop()
            # time.sleep(1)
            break

        # if framecounter > 50:
        #     break

    # cmd.disarm()
    # t.join(timeout=5)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    rs = RunSim("AirSimNH", settings=config_dir() / "airsim_settings_high_res.json")
    asyncio.run(main())
    rs.exit()
