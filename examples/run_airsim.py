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

rs = RunSim("AirSimNH")
# rs = RunSim("AirSimNH", settings=find_config_dir() / "settings.json")

asc = AirSimClient()
cmd = DroneCommands()

framecounter = 1
cam_num = 0
cams = ['down', "front", "right", "left"]

if True:
    while (True):
        framecounter += 1
        state = asc.getMultirotorState()
        pos = state.kinematics_estimated.position
        try:
            img = asc.get_image(cams[cam_num], rgb2bgr=False)
            puttext(img, f"Frame: {framecounter} Pos: {pos.x_val:.2f}, {pos.y_val:.2f}, {pos.z_val:.2f}")

            img = resize(img, width=800)
            # log.update(f"Frame: {framecounter} Pos: {pos.x_val:.2f}, {pos.y_val:.2f}, {pos.z_val:.2f}")
            if framecounter % 100 == 0:
                print(f"Frame: {framecounter} Pos: {pos.x_val:.2f}, {pos.y_val:.2f}, {pos.z_val:.2f}")
            log.draw(img)
            cv2.imshow("Camera", img)
        except:
            cam_num = 0
            logger.warning(f"No image from {cams[cam_num]} , setting cam_num to 0")
            time.sleep(0.1)

        # video.add(img_bgr)
        k = cv2.waitKey(10)
        if k == ord('q') or k == ord('Q'):
            # logger.info("......cancelLastTask")
            cmd.cancel_last_task()
            # print(f"Landed state:  {state.landed_state}")
            if state.landed_state == 0:
                logger.info("Landed state = 0")
                # break

        if k == ord('c') or k == ord('C'):
            cam_num += 1
            if cam_num >= len(cams):
                cam_num = 0
            # log.update(f"Camera: {cams[cam_num]}")
            logger.info(f"Camera: {cams[cam_num]}")

        if k == ord('a') or k == ord('A'):
            logger.info("......Auto")
            try:
                cmd.start()
            except:
                logger.warning("Can't start, already flying?")

        if k == ord('t') or k == ord('T'):
            logger.info("......Takeoff")
            # cmd.arm()
            try:
                cmd.takeoff()
            except:
                logger.warning("Can't takeoff, already flying?")

        if k == ord('r') or k == ord('R'):
            logger.info("......Reset Position")
            try:
                cmd.reset_position()
            except Exception as e:
                logger.warning(f"On reset: {e} (Todo fix this)")  # todo error "IOLoop is already running" fix this

        if k == ord('p') or k == ord('P'):
            cmd.toggle_pause()


        if k == ord('s') or k == ord('S'):
            logger.info("......Stop")
            try:
                cmd.stop()
            except:
                logger.warning("Can't stop:?")

        if k == 27:
            cmd.stop()
            time.sleep(1)
            break

        # if framecounter > 50:
        #     break

cmd.disarm()
cmd.close()
# t.join(timeout=5)
cv2.destroyAllWindows()
rs.exit()
