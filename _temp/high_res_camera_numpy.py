import UAV.airsim_python_client as airsim
from datetime import datetime
import numpy as np
import cv2
import time

'''
Simple script with settings to create a high-resolution camera, and fetching its images, showing on opencv.
'''

def puttext(img: np.ndarray,
            text: str,
            color: tuple[int, int, int] = (0, 0, 255)) -> np.ndarray:
    height = img.shape[0]
    size = 2  # text size 1 = 22 pixels, want 70 % of patch
    thickness = 2
    (text_width, text_height) = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, size, thickness)[0]
    # pos = (img.shape[1] // 2 - text_width // 2, img.shape[0] // 2 + text_height // 2)
    pos = (text_width // 2, int(text_height *1.5))
    return cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, size, color, thickness, cv2.LINE_AA)



from UAV.utils.sim_linux import RunSim
# rs = RunSim("Coastline")
# rs = RunSim("LandscapeMountains")

# rs = RunSim("AirSimNH", settings="config/settings_high_res.json")
# rs = RunSim("AirSimNH", settings="config/settings_high_res.json")
# rs = RunSim("Blocks", settings="settings_arducopter.json")
rs = RunSim("AirSimNH", settings="config/settings_high_res.json")

# rs = RunSim("ZhangJiajie")
# rs = RunSim("Blocks")
# time.sleep(3)
# rs.place_object( "Car_01", 5.0, 0.0, -1.0,)
rs.place_object("Sofa_02", 5.0, 0.0, -1.0, 2)

# count = 0
# while count < 100:
#     time.sleep(0.1)
#     count += 1

client = rs.client
# client = airsim.VehicleClient()
# client.confirmConnection()

assets = client.simListAssets()
print(f"Assets: {assets}")

framecounter = 1
prevtimestamp = datetime.now()
img_rgb = np.zeros((720, 1280, 3), dtype=np.uint8)
while(True):
    responses = client.simGetImages([airsim.ImageRequest("high_res", airsim.ImageType.Scene, False, False)])
    # print("High resolution image captured.")
    response = responses[0]
    img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
    # reshape array to 4 channel image array H X W X 4
    img_rgb = img1d.reshape(response.height, response.width, 3)
    puttext(img_rgb, f"Frame: {framecounter}")
    cv2.imshow("Camera", img_rgb)
    k = cv2.waitKey(10)
    if k == ord('q') or k == ord('Q') or k == 27:
        break


    # if framecounter%30 == 0:
    #     now = datetime.now()
    #     print(f"Time spent for 30 frames: {now-prevtimestamp}")
    #     prevtimestamp = now

    # responses = client.simGetImages([airsim.ImageRequest("low_res", airsim.ImageType.Scene, False, False)])
    framecounter += 1

rs.exit()
cv2.destroyAllWindows()
