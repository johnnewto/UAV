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
    """Run the AIRsim simulator"""

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

        self.load_with_shell()
        time.sleep(3)
        self.client = airsim.VehicleClient()
        self.client.confirmConnection()
        self.objects = []
        # self.place_car(5.0, 0.0, -20.0)

    def load(self):
        """Load the simulator without shell"""
        if not is_process_running(f"{self.name}"):
            # avoid using the shell
            script_path = [f'/home/jn/Airsim/{self.name}/LinuxNoEditor/{self.name}/Binaries/Linux/{self.name}']
            if self.windowed is not None:
                script_path.append(f' -ResX={self.resx} -ResY={self.resy} -{self.windowed} ')
            if self.settings is not None:
                script_path.append(f' -settings={self.settings} ')

            print("Starting Airsim ", script_path)
            with TemporaryFile() as f:
                self.process = subprocess.Popen(script_path, stdout=f, stderr=f,)

            print("Started Airsim " + self.name)
        else:
            print(f"Airsim {self.name} already running.")
            
    def load_with_shell(self):
        """ load with shell"""
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
        find_and_terminate_process(self.name)
        print("Stopped Airsim")

        # self.process.terminate()
        # # self.process.kill()
        # try:
        #     self.process.wait(timeout=1.0)
        #     print('Airsim exited with rc =', self.process.returncode)
        # except subprocess.TimeoutExpired:
        #     print('subprocess did not terminate in time')
        #     # try to terminate it another way
        #     find_and_terminate_process(self.name)
        #     print("Stopped Airsim")

    def check_asset_exists(self,
                           name: str  # asset name
                           )->bool: # exists
        """Check if asset exists"""
        return name in self.client.simListAssets()

    def place_object(self,
                    name: str,  # asset name
                    x: float,  # position x
                    y: float,  # position y
                    z: float,  # position z
                    scale: float = 1.0,  # scale
                    physics_enabled: bool = False,  # physics enabled
                    ):

        """Place an asset in the simulator
            Checks to see if it exists first"""
        if not self.check_asset_exists(name):
            print(f"Asset {name} does not exist.")
            return
        desired_name = f"{name}_spawn_{random.randint(0, 100)}"
        pose = airsim.Pose(position_val=airsim.Vector3r(x, y, z), )
        scale = airsim.Vector3r(scale, scale, scale)
        self.objects.append(self.client.simSpawnObject(desired_name, name, pose, scale, physics_enabled))

    # def list_cameras(self):
    #     """List the cameras"""
    #     return self.client.simListCameras()

    def get_image(self, camera_name: str = "0"  # camera name
                  ) -> np.ndarray:  # image
        """Get an image from the simulator of camera `camera_name`"""
        responses = self.client.simGetImages([airsim.ImageRequest(camera_name, airsim.ImageType.Scene, False, False)])
        response = responses[0]
        img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
        img_rgb = img1d.reshape(response.height, response.width, 3)
        img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGB)
        return img_rgb

    def get_images(self, camera_names: list = ["0"]  # camera names
                   ) -> list[np.ndarray]:  # images
        """Get images from the simulator of cameras `camera_names`"""
        responses = self.client.simGetImages(
            [airsim.ImageRequest(camera_name, airsim.ImageType.Scene, False, False) for camera_name in camera_names])
        images = []
        for response in responses:
            img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
            img_rgb = img1d.reshape(response.height, response.width, 3)
            img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGB)
            images.append(img_rgb)
        return images
