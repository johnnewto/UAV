from UAV.mavlink._old_camera import CameraClient, CameraServer, MAVCom, boot_time_str, date_time_str, time_since_boot_ms, time_UTC_usec
from UAV.camera.fake_cam import GSTCamera, read_camera_dict_from_toml, CameraCaptureStatus

from pathlib import Path
import cv2




if __name__ == '__main__':
    print (f"{boot_time_str =}")
    config_path = Path("../config")
    with  GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml")) as cam_fake1:
        cam_fake1.image_start_capture(0.1, 5)

        while cam_fake1._image_capture_thread.is_alive():
            if cam_fake1.last_image is not None:
                cv2.imshow('image', cam_fake1.last_image)
                cam_fake1.last_image = None
            cv2.waitKey(10)
        print (f"Waiting for capture thread to finish")


