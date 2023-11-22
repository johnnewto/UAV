import cv2

from UAV.mavlink import CameraClient, CameraServer, MAVCom, GimbalClient, GimbalServer, mavutil, mavlink
from UAV.utils.general import boot_time_str, With, toml_load, config_dir

from UAV.cameras.gst_cam import GSTCamera
from gstreamer import GstPipeline, Gst, GstContext, GstPipes
import gstreamer.utils as gst_utils

import time
from pathlib import Path
import asyncio

SINK_PIPELINE = gst_utils.to_gst_string([
    'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
    'rtph264depay ! avdec_h264',
    'videoconvert',
    'fpsdisplaysink',
    # 'autovideosink',
])
con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"

print(f"{boot_time_str =}")

cam_uav = GSTCamera(camera_dict=toml_load(config_dir() / "test_cam_0.toml"))


async def doit():
    # with GstContext():  # GST main loop in thread
    with GstContext(), GstPipeline(
            SINK_PIPELINE):  # Create a Gstreamer pipeline to display the received video on fpsdisplaysink
        with MAVCom(con1, source_system=111, loglevel=10) as client:
            with MAVCom(con2, source_system=222) as server:
                gcs = client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=10))
                server.add_component(CameraServer(camera=cam_uav, source_component=mavlink.MAV_COMP_ID_CAMERA))
                # server.add_component(CameraServer(mav_type=MAV_TYPE_CAMERA, source_component=22, cameras=None, debug=False))

                ret = await gcs.wait_heartbeat(remote_mav_type=mavlink.MAV_TYPE_CAMERA)
                print(f"Heartbeat received {ret = }")
                time.sleep(10)
                msg = await gcs.request_message(mavlink.MAVLINK_MSG_ID_CAMERA_INFORMATION, target_system=222,
                                                target_component=mavlink.MAV_COMP_ID_CAMERA)
                print(f"1 MAVLINK_MSG_ID_CAMERA_INFORMATION {msg}")
                msg = await gcs.request_message(mavlink.MAVLINK_MSG_ID_STORAGE_INFORMATION, target_system=222,
                                                target_component=mavlink.MAV_COMP_ID_CAMERA)
                print(f"2 MAVLINK_MSG_ID_STORAGE_INFORMATION {msg}")
                msg = await gcs.request_message(mavlink.MAVLINK_MSG_ID_CAMERA_CAPTURE_STATUS, target_system=222,
                                                target_component=mavlink.MAV_COMP_ID_CAMERA)
                print(f"3 MAVLINK_MSG_ID_CAMERA_CAPTURE_STATUS {msg}")
                msg = await gcs.request_message(mavlink.MAVLINK_MSG_ID_CAMERA_SETTINGS, target_system=222,
                                                target_component=mavlink.MAV_COMP_ID_CAMERA)
                print(f"4 MAVLINK_MSG_ID_CAMERA_SETTINGS {msg}")

                ret = await gcs.image_start_capture(222, mavlink.MAV_COMP_ID_CAMERA, interval=0.2, count=5)
                print(f"{ret = }")

                # while cam_uav.pipeline.is_active():
                #     if cam_uav.last_image is not None:
                #         cv2.imshow('gst_src', cam_uav.last_image)
                #         cam_uav.last_image = None
                #     cv2.waitKey(10)
                #
                # start = time.time()
                time.sleep(1)
                msg = await gcs.request_message(mavlink.MAVLINK_MSG_ID_STORAGE_INFORMATION, target_system=222,
                                                target_component=mavlink.MAV_COMP_ID_CAMERA)
                print(f"5 MAVLINK_MSG_ID_STORAGE_INFORMATION {msg}")
                # print(f"request_storage_information time : {1000*(time.time() - start) = } msec")
                print(cam_uav.list_files())
                for file in cam_uav.list_files():

                    if file.endswith(".jpg"):
                        img = cam_uav.load_image_from_memoryfs(file)
                        print (f"{file = }, {img.shape = }")
                    cv2.waitKey(0)


                # time.sleep(5)
    # cv2.destroyAllWindows()


asyncio.run( doit())