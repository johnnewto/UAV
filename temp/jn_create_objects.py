
import airsim
import random
import time
from utils.sim import RunSim
# rs = RunSim("Coastline")
rs = RunSim("AirSimNH")

client = airsim.VehicleClient()
client.confirmConnection()
client.simPause(False)
assets = client.simListAssets()
print(f"Assets: {assets}")
# client.simSetCameraPose()

scale = airsim.Vector3r(1.0, 1.0, 1.0)

# asset_name = random.choice(assets)
asset_name = '1M_Cube_Chamfer'
asset_name = 'Car_01'

desired_name = f"{asset_name}_spawn_{random.randint(0, 100)}"
pose = airsim.Pose(position_val=airsim.Vector3r(5.0, 0.0, -20.0), )

obj_name = client.simSpawnObject(desired_name, asset_name, pose, scale, False)

print(f"Created object {obj_name} from asset {asset_name} "
      f"at pose {pose}, scale {scale}")



# rs.exit()