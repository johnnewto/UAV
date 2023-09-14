from UAV.mavlink.camera import CameraClient, CameraServer, FakeCamera, MAVCom, boot_time_str
from UAV.mavlink.component import Component, mavutil, mavlink
import time



MAV_TYPE_GCS = mavutil.mavlink.MAV_TYPE_GCS
MAV_TYPE_CAMERA = mavutil.mavlink.MAV_TYPE_CAMERA
# cli = GimbalClient(mav_connection=None, source_component=11, mav_type=MAV_TYPE_GCS, debug=False)
# gim1 = GimbalServer(mav_connection=None, source_component=22, mav_type=MAV_TYPE_CAMERA, debug=False)

con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"

if __name__ == '__main__':
    print (f"{boot_time_str =}")
    cam_fake1 = FakeCamera()

    with MAVCom(con1, source_system=111, debug=False) as client:
        with MAVCom(con2, source_system=222, debug=False) as server:
            cam:CameraClient = client.add_component(
                CameraClient(mav_type=MAV_TYPE_GCS, source_component=11, debug=False))
            server.add_component(CameraServer(mav_type=MAV_TYPE_CAMERA, source_component=22, camera=cam_fake1, debug=False))

            cam.wait_heartbeat(target_system=222, target_component=22, timeout=1)
            time.sleep(0.1)
            cam.set_target(222, 22)

            cam.request_storage_information()

            cam.request_camera_capture_status()

            cam.request_camera_information()

            cam.request_camera_settings()

            cam.image_start_capture(interval=0.1, count=10)

            time.sleep(2)
            start = time.time()
            cam.request_storage_information()
            print(f"request_storage_information time : {1000*(time.time() - start) = } msec")

