from UAV.mavlink.camera import CameraClient, CameraServer, MAVCom, boot_time_str
from UAV.mavlink.component import Component, mavutil, mavlink
from UAV.camera.fake_cam import CV2Camera, GSTCamera, read_camera_dict_from_toml
from gstreamer import  GstPipeline
import gstreamer.utils as gst_utils
import time
from pathlib import Path
import cv2

MAV_TYPE_GCS = mavutil.mavlink.MAV_TYPE_GCS
MAV_TYPE_CAMERA = mavutil.mavlink.MAV_TYPE_CAMERA
# cli = GimbalClient(mav_connection=None, source_component=11, mav_type=MAV_TYPE_GCS, debug=False)
# gim1 = GimbalServer(mav_connection=None, source_component=22, mav_type=MAV_TYPE_CAMERA, debug=False)
SINK_PIPELINE = gst_utils.to_gst_string([
            'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
            'rtph264depay ! avdec_h264',
            'fpsdisplaysink',
            # 'autovideosink',
        ])
con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"
con1 = "udpout:192.168.122.84:14445"
con1 = "udpout:localhost:14445"
if __name__ == '__main__':
    print (f"{boot_time_str =}")
    config_path = Path("../config")

    # cam_gst_1 = GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"))
    # cam_cv2_1 = CV2Camera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"))
    with GstPipeline(SINK_PIPELINE) as rcv_pipeline: # this will show the video on fpsdisplaysink
        with MAVCom(con1, source_system=111, debug=False) as client:
            with MAVCom(con2, source_system=222, debug=False) as server:
                cam:CameraClient = client.add_component(
                    CameraClient(mav_type=MAV_TYPE_GCS, source_component=11, debug=False))
                # server.add_component(CameraServer(mav_type=MAV_TYPE_CAMERA, source_component=22, camera=cam_gst_1, debug=False))
                # server.add_component(CameraServer(mav_type=MAV_TYPE_CAMERA, source_component=22, camera=None, debug=False))

                cam.wait_heartbeat(target_system=222, target_component=22, timeout=1)
                time.sleep(0.1)
                cam.set_target(222, 22)


                cam.request_camera_information()
                time.sleep(0.1)

                cam.request_storage_information()

                cam.request_camera_capture_status()

                cam.request_camera_information()

                cam.request_camera_settings()

                cam.image_start_capture(interval=0.1, count=10)

                # while cam_gst_1.capture_thread.is_alive():
                #     if cam_gst_1.last_image is not None:
                #         cv2.imshow('gst_src', cam_gst_1.last_image)
                #         cam_gst_1.last_image = None
                #     cv2.waitKey(10)

                time.sleep(2)
                start = time.time()
                msg = cam.request_storage_information()
                print (msg)
                print(f"request_storage_information time : {1000*(time.time() - start) = } msec")

