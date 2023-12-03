import time

import cv2

from gstreamer import GstContext
from UAV.cameras.gst_cam import GSTCamera, logging
from UAV.logging import LogLevels
from UAV.mavlink import CameraServer, MAVCom, mavlink
from UAV.mavlink.gimbal_server_viewsheen import GimbalServerViewsheen
from UAV.utils import config_dir, boot_time_str, toml_load
import platform
import subprocess
from pathlib import Path

print(platform.processor())

# cli = GimbalClient(mav_connection=None, source_component=11, mav_type=MAV_TYPE_GCS, debug=False)
# gim1 = GimbalServer(mav_connection=None, source_component=22, mav_type=MAV_TYPE_CAMERA, debug=False)

# con2 = "udpout:10.42.0.1:14445"
# con2 = "udpout:192.168.1.175:14445"
# con2 = "udpout:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"

# ENCODER = '265enc'
ENCODER = ''

def config_dir():
    return Path(__file__).parent.parent / "config"


if __name__ == '__main__':

    # subprocess.run(["ls", "-l"]) 

    logging.info(f"boot_time_str = {boot_time_str = }")
    # p = subprocess.run(["ls", "-l"])
    # print(f"ret = {p.returncode = }")

    mach = 'jetson' if platform.processor() == 'aarch64' else 'test'
    con2 = "udpout:192.168.1.175:14445" if mach == 'jetson' else "udpout:localhost:14445"
    con2 = "/dev/ttyUSB0"
    print(f"{mach}, {config_dir() = }")

    config_dict = toml_load(config_dir() / f"{mach}_server_config.toml")
    print(config_dict)

    print("Starting GSTCameras")
    cam_0 = GSTCamera(config_dict, camera_dict=toml_load(config_dir() / f"{mach}_cam_0.toml"), loglevel=LogLevels.INFO)
    cam_1 = GSTCamera(config_dict, camera_dict=toml_load(config_dir() / f"{mach}_cam_1.toml"), loglevel=LogLevels.INFO)
    cam_2 = GSTCamera(config_dict, camera_dict=toml_load(config_dir() / f"viewsheen.toml"), loglevel=LogLevels.INFO)

    print("*** Starting MAVcom")
    try:
        UAV_server = MAVCom(con2, source_system=222, loglevel=LogLevels.INFO)
    except Exception as e:
        print(f"*** MAVCom failed to start: {e} **** ")
        cam_0.close()
        cam_1.close()
        cam_2.close()
        exit(1)

    with GstContext():
        with UAV_server:  # This normally runs on drone
            # UAV_server.add_component(CameraServer(mav_type=MAV_TYPE_CAMERA, source_component=22, camera=cam_gst_1))
            UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_0, loglevel=20))
            UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA2, camera=cam_1, loglevel=20))
            UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA3, camera=cam_2, loglevel=20))

            UAV_server.add_component(GimbalServerViewsheen(mav_type=mavlink.MAV_TYPE_GIMBAL, source_component=mavlink.MAV_COMP_ID_GIMBAL, loglevel=20))

            last_time = time.time()
            bitrate = 1000000

            # cam_0.image_start_capture(1,100)
            # cam_0.video_start_streaming()
            # cam_1.video_start_streaming()
            # cam_2.video_start_streaming()

            while cam_1.pipeline:
                # if time.time() - last_time > 10:
                #     last_time = time.time()
                #     encoder0 = cam_0._pipeline_stream_udp.pipeline.get_by_name("encoder")
                #     encoder1 = cam_1._pipeline_stream_udp.pipeline.get_by_name("encoder")
                #     bitrate = 4000000 if bitrate != 4000000 else 100000
                #     encoder0.set_property("bitrate", bitrate)
                #     encoder1.set_property("bitrate", bitrate*2)
                #     print(f"{bitrate = }")
                if cam_1.last_image is not None:
                    pass
                    # cv2.imshow('gst_src', cam_1.last_image)
                    # cam_1.last_image = None
                    # cv2.waitKey(10)
                time.sleep(0.01)

    cv2.destroyAllWindows()
    time.sleep(0.01)
    cam_0.close()
    cam_1.close()
    cam_2.close()
