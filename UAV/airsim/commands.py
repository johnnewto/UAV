__all__ = ['logger', 'start_sim', 'DroneCommands']

import sys
import threading

from .client import AirSimClient
import UAV.airsim_python_client as airsim
import UAV.params as params
import time
from ..utils.sim_linux import RunSim, is_process_running, find_and_terminate_process
import logging

logging.basicConfig(format='%(asctime)-8s,%(msecs)-3d %(levelname)5s [name] [%(filename)10s:%(lineno)3d] %(message)s',
                    datefmt='%H:%M:%S',
                    level=params.LOGGING_LEVEL)
logger = logging.getLogger(params.LOGGING_NAME)


def start_sim():
    """Start the Airsim simuator if it is not already running"""
    sim_name = "AirSimNH"
    if not is_process_running(f"{sim_name}"):
        return RunSim("AirSimNH", settings="config/settings_high_res.json")
    return None


class DroneCommands():
    """Class Multirotor Client for the Airsim simulator with higher level procedures"""

    def __init__(self,
                 takeoff_z: int = -5):  # takeoff Height
        self._z = takeoff_z
        self._stop = False
        self._client = None
        self._client = AirSimClient()
        self._t = None
        self._evt_no_pause = threading.Event()
        self._evt_no_pause.set()
        time.sleep(0.1)  # let AirSimClient

    def start(self):
        """Start the drone on a path in the Airsim simulator.
        Creates a client and connects to the simulator."""
        # if self._t is None and not self._t.is_alive:

        try:
            if self._t.is_alive():
                logger.warning("DroneCommands() thread already running")
                return self
        except:
            pass

        self._t = threading.Thread(target=self.do_tasklist, daemon=True)
        self._t.start()
        logger.info("DroneCommands() thread started")

        return self

    def cancel_last_task(self):
        """Cancel the last task"""
        self._client.cancelLastTask()

    def arm(self):
        """Run the drone on a path in the Airsim simulator.
            Creates a client and connects to the simulator."""
        if self._client is None:
            self._client = AirSimClient()

        self._client.enableApiControl(True)

        logger.info("Arming the drone...")
        self._client.armDisarm(True)

    def disarm(self):
        """Disarm the drone and disconnect from the simulator"""
        logger.info("disarming...")
        self._client.armDisarm(False)
        self._client.enableApiControl(False)

    def takeoff(self):
        """Takeoff to the takeoff height"""
        state = self._client.getMultirotorState()
        if state.landed_state == airsim.LandedState.Landed:
            logger.info("taking off...")
            self._client.takeoffAsync().join()
        else:
            self._client.hoverAsync().join()

        time.sleep(0.1)

        state = self._client.getMultirotorState()
        if state.landed_state == airsim.LandedState.Landed:
            logger.info("take off failed...")
            sys.exit(1)

        # AirSim uses NED coordinates so negative axis is up.
        # _z of -5 is 5 meters above the original launch point.
        # _z = -50
        print("make sure we are hovering at {} meters...".format(-self._z))
        self._client.moveToZAsync(self._z, 10).join()

    def do_NH_path(self):
        """Fly on a path in the Airsim simulator"""
        logger.info("flying on path...")
        print("""This script is designed to fly on the streets of the Neighborhood environment
            and assumes the unreal position of the drone is [160, -1500, 120].""")
        result = self._client.moveOnPathAsync([airsim.Vector3r(125, 0, self._z),
                                               airsim.Vector3r(125, -130, self._z),
                                               airsim.Vector3r(0, -130, self._z),
                                               airsim.Vector3r(0, 0, self._z)],
                                              8, 120,
                                              airsim.DrivetrainType.ForwardOnly, airsim.YawMode(False, 0), 20, 1).join()

    def rth(self):
        logger.info("returning home...")
        # drone will over-shoot so we bring it back to the start point before landing.
        # _client.moveToPositionAsync(0,0,_z,1).join()
        self._client.goHomeAsync().join()

    def land(self):
        logger.info("landing...")
        self._client.landAsync().join()

    def pause(self):
        logger.info("pausing...(cancelLastTask and hover)")
        self._evt_no_pause.clear()
        try:
            self._client.cancelLastTask().join()
        except Exception as e:
            print(e)
        try:
            self._client.hoverAsync().join()
        except Exception as e:
            print(e)
        try:
            self._client.moveToZAsync(-20, 10).join()
        except Exception as e:
            print(e)

    def resume(self):
        """Resume the tasks"""
        logger.info("resuming...")
        self._evt_no_pause.set()
        # self._t = threading.Thread(target=self.do_tasklist, daemon=True)
        # self._t.start()

    def toggle_pause(self):
        """Toggle the pause state"""
        if self._evt_no_pause.is_set():
            self.pause()
        else:
            self.resume()

    def do_tasklist(self):
        """Run a list of tasks in order"""
        tasks = [self.arm, self.takeoff, self.do_NH_path, self.rth, self.land, self.disarm]
        self._stop = False
        self._evt_no_pause.set()
        for task in tasks:
            self._evt_no_pause.wait()
            if self._stop:
                break
            logger.info(f"Running task: {task.__name__}")
            task()
        logger.info("All Tasks finished.")

    def reset_position(self):
        """Reset the drone to the original position"""
        self.stop()
        self._client.reset()
        # self._client.enableApiControl(True)
        # self._client.armDisarm(True)
        # self._client.takeoffAsync().join()
        # self._client.moveToZAsync(self._z, 5).join()

    def stop(self):
        """ stop the client by cancelling the last task and exiting the do_tasklist loop """
        self._stop = True
        self._evt_no_pause.set()
        try:
            self._client.cancelLastTask()
        except Exception as e:
            print(e)

    def close(self):
        """Close the client"""
        self.stop()
        try:
            self._t.join(timeout=5)
        except Exception as e:
            logger.warning(f'Closing DroneCommands() thread: "{e}"')
