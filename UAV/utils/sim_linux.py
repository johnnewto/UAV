__all__ = ["RunSim", "is_process_running", "find_and_terminate_process", "sim_names", "airsim"]

import random
import subprocess
import time
import numpy as np
import cv2
import UAV
import UAV.airsim_python_client as airsim
import psutil

from pathlib import Path
from tempfile import TemporaryFile

sim_names = ["AirSimNH", "LandscapeMountains", "Blocks", "Coastline"]


# process_name_to_terminate = 'LandscapeMountains'
# Find and terminate the process
# find_and_terminate_process(process_name_to_terminate)

def is_process_running(process_name):
    # Iterate through all running processes
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            return True
    return False


def find_and_terminate_process(process_name):
    # Iterate through all running processes and terminate the one with process_name
    for process in psutil.process_iter(['pid', 'name']):

        if process.info['name'] == process_name:
            # print(process.info['name'])
            try:
                # Terminate the process gracefully (you can use process.kill() for forceful termination)
                process.terminate()
                print(f"Terminated process {process_name} with PID {process.info['pid']}")
            except psutil.NoSuchProcess:
                pass


class RunSim:
    """Run the Airsim simulator"""

    def __init__(self,
                 name: str = "Coastline",  # name of the simulator environment
                 resx: int = 800,  # window size  x
                 resy: int = 600,  # window size  y
                 windowed: str | None = 'windowed',  # windowed or fullscreen
                 settings: str = "settings.json"):  # settings file

        # self.settings = f"/home/$USER/Documents/AirSim/{settings}"
        if Path(settings).is_file():
            self.settings = settings
        elif Path(f"{UAV.UAV_DIR}/{settings}").is_file():
            self.settings = f"{UAV.UAV_DIR}/{settings}"
        else:
            self.settings = None
            print(f"Settings file {settings} not found.")
            # assert False
        # self.settings = f"{Path.cwd()}/{settings}"
        # self.settings = settings
        # print(self.settings)
        self.name = name
        self.resx = resx
        self.resy = resy
        self.windowed = windowed
        # self.load_with_shell()
        self.load()
        time.sleep(3)

        # self.client = airsim.MultirotorClient()
        # self.client.confirmConnection()

        self._shell = False

    def load(self):
        """Load the simulator without shell"""
        self._shell = False
        if not is_process_running(f"{self.name}"):
            # avoid using the shell
            script_path = [f'/home/jn/Airsim/{self.name}/LinuxNoEditor/{self.name}/Binaries/Linux/{self.name}']
            if self.windowed is not None:
                script_path.append(f'-ResX={self.resx}')
                script_path.append(f'-ResY={self.resy}')
                script_path.append(f'-{self.windowed}')
            if self.settings is not None:
                script_path.append(f'-settings={self.settings}')

            print("Starting Airsim ", script_path)
            with TemporaryFile() as f:
                self.process = subprocess.Popen(script_path, stdout=f, stderr=f,)

            print("Started Airsim " + self.name)
        else:
            print(f"Airsim {self.name} already running.")
            
    def load_with_shell(self):
        """ load with shell, this is needed for `*.sh` files"""
        self._shell = True
        if not is_process_running(f"{self.name}"):

            script_path = f'/home/jn/Airsim/{self.name}/LinuxNoEditor/{self.name}.sh '
            if self.windowed is not None:
                script_path += f' -ResX={self.resx} -ResY={self.resy} -{self.windowed} '
            if self.settings is not None:
                script_path += f' -settings={self.settings} '

            print("Starting Airsim ", script_path)

            with TemporaryFile() as f:
                self.process = subprocess.Popen([script_path], shell=True, text=True)

            print("Started Airsim " + self.name)
        else:
            print(f"Airsim {self.name} already running.")

    def exit(self):
        """Exit the simulator"""
        if self._shell:
            find_and_terminate_process(self.name)
            print("Stopped Airsim")
            return

        self.process.terminate()
        # self.process.kill()
        try:
            self.process.wait(timeout=5.0)
            print('Airsim exited with rc =', self.process.returncode)
        except subprocess.TimeoutExpired:
            print('subprocess did not terminate in time')
            # # try to terminate it another way
            # find_and_terminate_process(self.name)
            # print("Stopped Airsim")


# Now mived to notebook
# class AirSimClient(airsim.MultirotorClient, object):
#     """Multirotor Client for the Airsim simulator with higher level procedures"""
#
#     def __init__(self, ip = "", port = 41451, timeout_value = 3600):
#         super(AirSimClient, self).__init__(ip, port, timeout_value)
#     # def __init__(self):
#     #     # super().MultirotorClient()
#         super().confirmConnection()
#         self.objects = []
#
#     def check_asset_exists(self,
#                            name: str  # asset name
#                            )->bool: # exists
#         """Check if asset exists"""
#         return name in super().simListAssets()
#
#     def place_object(self,
#                     name: str,  # asset name
#                     x: float,  # position x
#                     y: float,  # position y
#                     z: float,  # position z
#                     scale: float = 1.0,  # scale
#                     physics_enabled: bool = False,  # physics enabled
#                     ):
#
#         """Place an object in the simulator
#             First check to see if the asset it is based on exists"""
#         if not self.check_asset_exists(name):
#             print(f"Asset {name} does not exist.")
#             return
#         desired_name = f"{name}_spawn_{random.randint(0, 100)}"
#         pose = airsim.Pose(position_val=airsim.Vector3r(x, y, z), )
#         scale = airsim.Vector3r(scale, scale, scale)
#         self.objects.append(super().simSpawnObject(desired_name, name, pose, scale, physics_enabled))
#
#     # def list_cameras(self):
#     #     """List the cameras"""
#     #     return self.client.simListCameras()
#
#     def get_image(self, camera_name: str = "0",  # camera name
#                   rgb2bgr: bool = False,  # convert to bgr
#                   ) -> np.ndarray:  # image
#         """Get an image from the simulator of camera `camera_name`"""
#         responses = super().simGetImages([airsim.ImageRequest(camera_name, airsim.ImageType.Scene, False, False)])
#         response = responses[0]
#         img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
#         img = img1d.reshape(response.height, response.width, 3)
#         if rgb2bgr:
#             img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
#         return img
#
#     def get_images(self, camera_names: list = ["0"],  # camera names
#                    rgb2bgr: bool = False,  # convert to rgb
#                    ) -> list[np.ndarray]:  # images
#         """Get images from the simulator of cameras `camera_names`"""
#         responses = super().simGetImages(
#             [airsim.ImageRequest(camera_name, airsim.ImageType.Scene, False, False) for camera_name in camera_names])
#         images = []
#         for response in responses:
#             img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
#             img = img1d.reshape(response.height, response.width, 3)
#             if rgb2bgr:
#                 img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#             images.append(img)
#         return images