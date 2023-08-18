_all_ = ['start_sim', 'takeoff', 'do_path', 'land', 'do_all', 'stop']

import UAV.airsim_python_client as airsim
from UAV.airsim_client import AirSimClient
from datetime import datetime
import numpy as np
import sys
import time

from UAV.utils.sim_linux import RunSim, is_process_running, find_and_terminate_process

_client = None
_z = -5
_stop = False
def start_sim():
    """Start the Airsim simuator if it is not already running"""
    sim_name = "AirSimNH"
    if not is_process_running(f"{sim_name}"):
        return RunSim("AirSimNH", settings="config/settings_high_res.json")
    return None


def arm():
    """Run the drone on a path in the Airsim simulator"""
    global _client
    _client = AirSimClient()
    print("""This script is designed to fly on the streets of the Neighborhood environment
    and assumes the unreal position of the drone is [160, -1500, 120].""")
    _client.enableApiControl(True)

    print("arming the drone...")
    _client.armDisarm(True)


def takeoff():
    state = _client.getMultirotorState()
    if state.landed_state == airsim.LandedState.Landed:
        print("taking off...")
        _client.takeoffAsync().join()
    else:
        _client.hoverAsync().join()

    time.sleep(1)

    state = _client.getMultirotorState()
    if state.landed_state == airsim.LandedState.Landed:
        print("take off failed...")
        sys.exit(1)

    # AirSim uses NED coordinates so negative axis is up.
    # _z of -5 is 5 meters above the original launch point.
    # _z = -50
    print("make sure we are hovering at {} meters...".format(-_z))
    _client.moveToZAsync(_z, 5).join()


def do_NH_path():
    print("flying on path...")
    result = _client.moveOnPathAsync([airsim.Vector3r(125,0,_z),
                                    airsim.Vector3r(125,-130,_z),
                                    airsim.Vector3r(0,-130,_z),
                                    airsim.Vector3r(0,0,_z)],
                            12, 120,
                            airsim.DrivetrainType.ForwardOnly, airsim.YawMode(False,0), 20, 1).join()


def rth():
    print("returning home...")
    # drone will over-shoot so we bring it back to the start point before landing.
    # _client.moveToPositionAsync(0,0,_z,1).join()
    _client.goHomeAsync().join()

def land():
    print("landing...")
    _client.landAsync().join()


def disarm():
    print("disarming...")
    _client.armDisarm(False)
    _client.enableApiControl(False)

def stop():
    """ stop the client by exiting the do_all loop  and cancelling the last task """
    global _stop
    _stop = True
    _client.cancelLastTask()

def do_all():
    tasks = [arm, takeoff, do_NH_path, rth, land, disarm]
    for task in tasks:
        if _stop:
            break
        task()


if __name__ == '__main__' :
    start_sim()
    do_all()


