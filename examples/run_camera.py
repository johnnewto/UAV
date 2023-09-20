

from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil
from UAV.utils.general import boot_time_str

from UAV.camera import GSTCamera, read_camera_dict_from_toml
from gstreamer import  GstPipeline, Gst, GstContext
import gstreamer.utils as gst_utils
import time
from pathlib import Path
# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)

GCS_DISPLAY_PIPELINE = gst_utils.to_gst_string([
            'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
            'queue ! rtph264depay ! avdec_h264',
            'fpsdisplaysink',
        ])
con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"
# con1 = "udpin:192.168.122.84:14445"
if __name__ == '__main__':
    print (f"{boot_time_str =}")
    config_path = Path("../config")
    with GstContext(debug=False):  # GST main loop in thread
        with GstPipeline(GCS_DISPLAY_PIPELINE, debug=False) as rcv_pipeline: # this will show the video on fpsdisplaysink
            with MAVCom(con1, source_system=111, debug=False) as GCS_client: # This normally runs on GCS
                with MAVCom(con2, source_system=222, debug=False) as UAV_server: # This normally runs on drone
                    # add GCS manager
                    gcs = GCS_client.add_component( CameraClient(mav_type=mavutil.mavlink.MAV_TYPE_GCS, source_component=11, debug=False) )
                    # add UAV cameras, This normally runs on drone
                    cam_1 = GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"), debug=False)
                    UAV_server.add_component( CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component=22, camera=cam_1, debug=False))
                    cam_2 = GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"), debug=False)
                    UAV_server.add_component(CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component=23, camera=None, debug=False))
                    gimbal_cam_3 = UAV_server.add_component(GimbalServer(mav_type=mavutil.mavlink.MAV_TYPE_GIMBAL, source_component=24, debug=False))
                    # GCS client requests
                    gcs.wait_heartbeat(target_system=222, target_component=22, timeout=1)
                    # gcs.set_target(222, 22)

                    gcs.request_camera_information(222, 23)
                    gcs.request_camera_settings(222, 22)

                    # capture 5 images from camera 22 and 23
                    gcs.image_start_capture(222, 22, interval=1, count=5)
                    gcs.image_start_capture(222, 23, interval=1, count=5)

                    # Start & stop drone video capture
                    gcs.video_start_capture(222, 22, frequency=1)
                    time.sleep(5)
                    gcs.video_stop_capture(222, 22)
                    time.sleep(1)

                    # Start & stop drone video streaming camera 22
                    for i in range (2):
                        gcs.video_start_streaming(222, 22)
                        time.sleep(1)
                        gcs.request_storage_information(222, 22)
                        gcs.video_stop_streaming(222, 22)
                        gcs.request_camera_information(222, 22)
                        time.sleep(1)
                        gcs.request_camera_capture_status(222, 22)








if __name__ == '__main__':
    pass

# time.sleep(4)
# time.sleep(0.1)
# while cam_gst_1._image_capture_thread is None:
#     time.sleep(0.1)
# while cam_gst_1._image_capture_thread.is_running():
#     if cam_gst_1.last_image is not None:
#         cv2.imshow('gst_src', cam_gst_1.last_image)
#         cam_gst_1.last_image = None
#     cv2.waitKey(10)
#
# time.sleep(1)
# start = time.time()
# msg = cam.request_storage_information()
# print (msg)
# print(f"request_storage_information time : {1000*(time.time() - start) = } msec")