from UAV.logging import LogLevels

from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil, mavlink
from UAV.utils.general import boot_time_str
from UAV.mavlink.camera_client import CAMERA_IMAGE_CAPTURED

from UAV.camera import GSTCamera, read_camera_dict_from_toml
from gstreamer import  GstPipeline, Gst, GstContext
import gstreamer.utils as gst_utils
import time
from pathlib import Path
import asyncio

# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)

GCS_DISPLAY_PIPELINE = gst_utils.to_gst_string([
            'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
            'queue ! rtph264depay ! avdec_h264',
            'fpsdisplaysink',
        ])
con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"
# con1 = "udpin:192.168.122.84:14445"


# async def main():
#     ret = gcs.image_start_capture(222, 22, interval=1, count=5)
#     print(f"{ret = }")
#     #
#     # ret = await gcs.image_start_capture(222, 22, interval=1, count=5)
#     # print(f"{ret = }")
#
#     # ret = await  gcs.video_start_capture(222, 22, frequency=1)
#
#     await asyncio.sleep(5)

# def run_gui():
#     asyncio.run(main())


# if __name__ == '__main__':
async def main():
    # logger.disabled = True
    print (f"{boot_time_str =}")
    config_path = Path("../config")
    with GstContext(loglevel=LogLevels.INFO):  # GST main loop in thread
        with GstPipeline(GCS_DISPLAY_PIPELINE, loglevel=LogLevels.CRITICAL) as rcv_pipeline: # this will show the video on fpsdisplaysink
            # rcv_pipeline.log.disabled = True
            with MAVCom(con1, source_system=111, loglevel=LogLevels.CRITICAL) as GCS_client: # This normally runs on GCS
                with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server: # This normally runs on drone
                    # UAV_server.log.disabled = True
                    # GCS_client.log.disabled = True

                    # add GCS manager
                    gcs:CameraClient = GCS_client.add_component( CameraClient(mav_type=mavutil.mavlink.MAV_TYPE_GCS, source_component=11, loglevel=LogLevels.INFO) )
                    # gcs.log.disabled = True
                    # add UAV cameras, This normally runs on drone
                    cam_1 = GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"), loglevel=LogLevels.INFO)
                    # cam_1.log.disabled = True
                    cam_2 = GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"), loglevel=LogLevels.INFO)
                    UAV_server.add_component( CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component=22, camera=cam_1, loglevel=LogLevels.INFO))
                    UAV_server.add_component(CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component=23, camera=None, loglevel=LogLevels.INFO))
                    UAV_server.add_component(CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component=24, camera=None, loglevel=LogLevels.INFO))

                    # gimbal_cam_3 = UAV_server.add_component(GimbalServer(mav_type=mavutil.mavlink.MAV_TYPE_GIMBAL, source_component=24, debug=False))
                    # GCS client requests
                    # ret = await gcs.wait_heartbeat(target_system=222, target_component=22, timeout=1)
                    # print(f"Heartbeat 22 {ret = }")
                    event_new_cam = asyncio.Event()
                    cameras = []
                    async def find_cameras():
                        count = 0
                        while True:
                            ret = await gcs.wait_heartbeat(remote_mav_type=mavutil.mavlink.MAV_TYPE_CAMERA , timeout=2)
                            if ret:
                                if ret not in cameras:
                                    cameras.append(ret)
                                    event_new_cam.set()
                                    print (f"Found new camera {ret = }")
                                else:
                                    # if no new camera found in 3 seconds then break
                                    count += 1


                    async def test1(comp):
                        ret = await gcs.wait_heartbeat(target_system=222, target_component=comp, timeout=1)
                        print (f"Heartbeat {comp} {ret = }")
                        ret = await gcs.image_start_capture(222, comp, interval=0.2, count=5)
                        print (f"Image Capture {comp = } {ret = }")
                        while True:
                            ret = await gcs.Await_for_message(mavlink.MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED, 222, comp, 2)
                            print (f"Image Request {comp = } {ret = }")
                            if not ret:
                                print (f"BREAK Image Request {comp = } {ret = }")
                                break
                            # await asyncio.sleep(1)
                        # await asyncio.sleep(5)

                    async def test2(comp):
                        for i in range (10):
                            ret = await gcs.wait_heartbeat(target_system=222, target_component=comp, timeout=2)
                            print (f"Heartbeat {comp} {ret = }")

                    async def test3(task):
                        await asyncio.sleep(3)

                        print(f"Cancelling {task = }")
                        task.cancel()

                        print (f"Cancelled {task = }")

                    # gcs.set_target(222, 22)
                    #
                    # gcs.request_camera_information(222, 23)
                    # gcs.request_camera_settings(222, 22)
                    #
                    # # capture 5 images from camera 22 and 23
                    # while True:
                    #     ret = await gcs.image_start_capture(222, 22, interval=1, count=5)
                    #     print(f"{ret = }")
                    #     await asyncio.sleep(1)
                    # ret = await gcs.image_start_capture(222, 23, interval=1, count=5)
                    # print(f"{ret = }")
                    fc_task = asyncio.create_task(find_cameras())
                    tasks = []

                    # tasks.append(asyncio.create_task(gcs.wait_heartbeat(target_system=222, target_component=22, timeout=1)))
                    # # tasks.append(asyncio.create_task(gcs.wait_heartbeat(target_system=222, target_component=23, timeout=1)))
                    # # tasks.append(asyncio.create_task(gcs.image_start_capture(222, 22, interval=0.2, count=5)))
                    tasks.append(asyncio.create_task(test1(22)))
                    # t = asyncio.create_task(test2(23))
                    # tasks.append(t)
                    # tasks.append(asyncio.create_task(test3(t)))
                    try:
                        await asyncio.gather(*tasks)
                    except asyncio.CancelledError as e:
                        print (f"CancelledError {e = }")

                    fc_task.cancel()
                    # await asyncio.gather(*tasks)

                    # ret = await gcs.image_start_capture(222, 22, interval=0.2, count=5)
                    # print(f"{ret = }")
                    # await asyncio.sleep(1)
                    # asyncio.run(main())
                    #
                    # ret = await gcs.image_start_capture(222, 22, interval=1, count=5)
                    # print(f"{ret = }")

                    # ret = await  gcs.video_start_capture(222, 22, frequency=1)

                    # ret = gcs.image_start_capture(222, 22, interval=1, count=5)
                    # print (f"{ret = }")
                    #
                    # time.sleep(5)

                    # gcs.image_start_capture(222, 22, interval=1, count=5)  # todo wait for first capture to finish
                    # gcs.image_start_capture(222, 22, interval=1, count=5)
                    #
                    #
                    # time.sleep(5)
                    # UAV_server.component[22].camera.list_files()
                    # # # # gcs.image_start_capture(222, 23, interval=1, count=5)
                    # # #
                    # # #
                    # # # # Start & stop drone video capture
                    # gcs.video_start_capture(222, 22, frequency=1)
                    # time.sleep(2)
                    # gcs.video_stop_capture(222, 22)   # todo create new file on drone
                    # time.sleep(1)
                    # # #
                    # # UAV_server.component[22].camera.list_files()
                    # # # Start & stop drone video streaming camera 22
                    # for i in range (2):
                    #     gcs.video_start_streaming(222, 22)
                    #     time.sleep(1)
                    #     # gcs.request_storage_information(222, 22)
                    #     gcs.video_stop_streaming(222, 22)
                    #     # gcs.request_camera_information(222, 22)
                    #     time.sleep(1)
                    #     gcs.request_camera_capture_status(222, 22)
                    #
                    # time.sleep(2)
                    # UAV_server.component[22].camera.list_files()
                    # gcs.video_start_streaming(222, 22)
                    # gcs.video_start_streaming(222, 22)
                    # time.sleep(2)
                    # # gcs.request_storage_information(222, 22)
                    # gcs.video_stop_streaming(222, 22)

if __name__ == '__main__':
    asyncio.run(main())

