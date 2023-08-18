import UAV.airsim_python_client as airsim
from UAV.airsim_client import AirSimClient
from datetime import datetime
import numpy as np
import cv2
import time


import sys
import time
from UAV.utils.sim_linux import RunSim, is_process_running, find_and_terminate_process

def run_video():
    #
    client = AirSimClient()

    print("""This script is designed to fly on the streets of the Neighborhood environment
    and assumes the unreal position of the drone is [160, -1500, 120].""")
    #
    # client = airsim.MultirotorClient()
    # client.confirmConnection()
    client.enableApiControl(True)

    print("arming the drone...")_all_ = ['start_sim', 'takeoff', 'do_path', 'land', 'do_all']

import UAV.airsim_python_client as airsim
from UAV.airsim_client import AirSimClient
from datetime import datetime
import numpy as np
import cv2
import time


import sys
import time
from UAV.utils.sim_linux import RunSim, is_process_running, find_and_terminate_process

client = None
z = -5
def start_sim():
    """Start the Airsim simulator if it is not already running"""
    sim_name = "AirSimNH"
    if not is_process_running(f"{sim_name}"):
        return RunSim("AirSimNH", settings="config/settings_high_res.json")
    return None


def arm():
    """Run the drone on a path in the Airsim simulator"""
    global client
    client = AirSimClient()
    print("""This script is designed to fly on the streets of the Neighborhood environment
    and assumes the unreal position of the drone is [160, -1500, 120].""")
    client.enableApiControl(True)

    print("arming the drone...")
    client.armDisarm(True)


def takeoff():
    state = client.getMultirotorState()
    if state.landed_state == airsim.LandedState.Landed:
        print("taking off...")
        client.takeoffAsync().join()
    else:
        client.hoverAsync().join()

    time.sleep(1)

    state = client.getMultirotorState()
    if state.landed_state == airsim.LandedState.Landed:
        print("take off failed...")
        sys.exit(1)

    # AirSim uses NED coordinates so negative axis is up.
    # z of -5 is 5 meters above the original launch point.
    # z = -50
    print("make sure we are hovering at {} meters...".format(-z))
    client.moveToZAsync(z, 5).join()


def do_path():
    print("flying on path...")
    result = client.moveOnPathAsync([airsim.Vector3r(125,0,z),
                                    airsim.Vector3r(125,-130,z),
                                    airsim.Vector3r(0,-130,z),
                                    airsim.Vector3r(0,0,z)],
                            12, 120,
                            airsim.DrivetrainType.ForwardOnly, airsim.YawMode(False,0), 20, 1).join()


def rth():
    print("returning home...")
    # drone will over-shoot so we bring it back to the start point before landing.
    # client.moveToPositionAsync(0,0,z,1).join()
    client.goHomeAsync().join()

def land():
    print("landing...")
    client.landAsync().join()


def disarm():
    print("disarming...")
    client.armDisarm(False)
    client.enableApiControl(False)

def do_all():
    arm()
    takeoff()
    do_path()
    rth()
    land()
    disarm()

if __name__ == '__main__' :
    start_sim()
    do_all()



    client.armDisarm(True)

    state = client.getMultirotorState()
    if state.landed_state == airsim.LandedState.Landed:
        print("taking off...")
        client.takeoffAsync().join()
    else:
        client.hoverAsync().join()

    time.sleep(1)

    state = client.getMultirotorState()
    if state.landed_state == airsim.LandedState.Landed:
        print("take off failed...")
        sys.exit(1)

    # AirSim uses NED coordinates so negative axis is up.
    # z of -5 is 5 meters above the original launch point.
    z = -50
    print("make sure we are hovering at {} meters...".format(-z))
    client.moveToZAsync(z, 5).join()

    # see https://github.com/Microsoft/AirSim/wiki/moveOnPath-demo

    # this method is async and we are not waiting for the result since we are passing timeout_sec=0.

    print("flying on path...")
    result = client.moveOnPathAsync([airsim.Vector3r(125,0,z),
                                    airsim.Vector3r(125,-130,z),
                                    airsim.Vector3r(0,-130,z),
                                    airsim.Vector3r(0,0,z)],
                            12, 120,
                            airsim.DrivetrainType.ForwardOnly, airsim.YawMode(False,0), 20, 1).join()

    # drone will over-shoot so we bring it back to the start point before landing.
    client.moveToPositionAsync(0,0,z,1).join()
    print("landing...")
    client.landAsync().join()
    print("disarming...")
    client.armDisarm(False)
    client.enableApiControl(False)
    # if rs is in locals then exit it, otherwise it will not exit
    # if 'rs' in locals():
    #     rs.exit()

    # cv2.destroyAllWindows()
    print("done.")
