import asyncio
import time

import gstreamer.utils as gst_utils
from UAV.cameras.gst_cam import GSTCamera
from UAV.logging import LogLevels
from UAV.mavlink import CameraClient, CameraServer, MAVCom, mavutil, mavlink
from UAV.mavlink.client_component import ClientComponent
from UAV.utils.general import boot_time_str, With, toml_load, config_dir, get_platform
from gstreamer import GstPipeline, Gst, GstContext, GstPipes
from gstreamer.utils import to_gst_string

DISPLAY_H264_PIPELINE = to_gst_string([
    'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
    'queue ! rtph264depay ! avdec_h264',
    'videoconvert',
    'fpsdisplaysink ',
])
# gst-launch-1.0 udpsrc port=5000 ! application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)RAW,sampling=(string)RGB ! rtpvrawdepay ! videoconvert ! autovideosink
DISPLAY_RAW_PIPELINE = to_gst_string([
    # 'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB,depth=(string)8, width=(string)640, height=(string)480, payload=(int)96',
    # 'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB,depth=(string)8, width=(string)640, height=(string)480',
    'udpsrc port={} caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB, depth=(string)8, width=(string)1920, height=(string)1080"',
    # 'udpsrc port={} caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB"',
    'queue ! rtpvrawdepay',
    # 'videorate',
    # 'video/x-raw,framerate=10/1',
    'videoconvert',
    'fpsdisplaysink sync=true ',
])

con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"

gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
# mach = get_platform()
# conf_path = config_dir()
# config_dict = toml_load(conf_path / f"{mach}_server_config.toml")
# mav_connection = config_dict['mavlink']['connection']
#
# print(f"{mach = }, {conf_path = } {mav_connection = }")
# print(config_dict)

# if __name__ == '__main__':
async def main(num_cams, udp_encoder):
    # logger.disabled = True
    print(f"{boot_time_str =}")
    server_config_dict = toml_load(config_dir() / f"test_server_config.toml")
    # if True:
    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread

        if '264' in udp_encoder:
            display_pipelines = [GstPipeline(DISPLAY_H264_PIPELINE.format(5000 + i)) for i in range(num_cams)]
        else:
            display_pipelines = [GstPipeline(DISPLAY_RAW_PIPELINE.format(5000 + i)) for i in range(num_cams)]
        # if True:
        with GstPipes(display_pipelines, loglevel=LogLevels.INFO):  # this will show the video on fpsdisplaysink
            with MAVCom(con1, source_system=111, loglevel=LogLevels.CRITICAL) as GCS_client:  # This normally runs on GCS
                with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server:  # This normally runs on drone

                    gcs: CameraClient = GCS_client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=LogLevels.DEBUG))

                    cam_1 = GSTCamera(server_config_dict, camera_dict=toml_load(config_dir() / "test_cam_0.toml"), udp_encoder=udp_encoder, loglevel=LogLevels.INFO)
                    # cam_2 = GSTCamera(server_config_dict, camera_dict=read_camera_dict_from_toml(find_config_dir() / "test_cam_0.toml"), udp_encoder=udp_encoder, loglevel=LogLevels.CRITICAL)

                    UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_1, loglevel=10))
                    contrl = UAV_server.add_component(ClientComponent(mav_type=mavlink.MAV_TYPE_ONBOARD_CONTROLLER, source_component=mavlink.MAV_COMP_ID_CAMERA, loglevel=10))

                    # UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component= mavlink.MAV_COMP_ID_CAMERA2, cameras=cam_2, loglevel=LogLevels.CRITICAL))
                    # UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=24, cameras=None, loglevel=LogLevels.WARNING))

                    # gimbal_cam_3 = UAV_server.add_component(GimbalServer(mav_type=mavutil.mavlink.MAV_TYPE_GIMBAL, source_component=24, debug=False))
                    # GCS client requests
                    # ret = await gcs.wait_heartbeat(remote_mav_type=mavlink.MAV_TYPE_CAMERA)
                    ret = await gcs.wait_heartbeat(target_system=222, target_component=mavlink.MAV_COMP_ID_CAMERA, timeout=1)


                    print(f"Heartbeat {ret = }")
                    # await asyncio.sleep(0.1)
                    msg = await gcs.request_message(mavlink.MAVLINK_MSG_ID_CAMERA_INFORMATION, target_system=222,
                                                    target_component=mavlink.MAV_COMP_ID_CAMERA)
                    print(f"1 MAVLINK_MSG_ID_CAMERA_INFORMATION {msg}")
                    msg = await gcs.request_message(mavlink.MAVLINK_MSG_ID_STORAGE_INFORMATION, target_system=222,
                                                    target_component=mavlink.MAV_COMP_ID_CAMERA)
                    print(f"2 MAVLINK_MSG_ID_STORAGE_INFORMATION  {msg}")
                    for i in range(2):
                        await gcs.video_start_streaming(222, mavlink.MAV_COMP_ID_CAMERA)
                        time.sleep(2)
                        await gcs.video_stop_streaming(222, mavlink.MAV_COMP_ID_CAMERA)
                        time.sleep(2)

                    # raise With.Break

                    #
                    # msg = await gcs.request_camera_information(222, 23)
                    # print (f"2 request_camera_information  = {msg} ")
                    #
                    #
                    # print(f"3 {await gcs.request_camera_information(222, 24)}")
                    # print()
                    # print()
                    await gcs.image_start_capture(222, mavutil.mavlink.MAV_COMP_ID_CAMERA, interval=0.2, count=5)
                    # await gcs.video_start_streaming(222, mavutil.mavlink.MAV_COMP_ID_CAMERA)

                    await asyncio.sleep(1)
                    # print("###### Shutdown  #################")
                    raise With.Break

                    for i in range(2):
                        await gcs.video_stop_streaming(222, mavutil.mavlink.MAV_COMP_ID_CAMERA2)
                        await gcs.video_start_streaming(222, mavutil.mavlink.MAV_COMP_ID_CAMERA)
                        await asyncio.sleep(2)
                        # gcs.request_storage_information(222, 22)
                        await gcs.video_stop_streaming(222, mavutil.mavlink.MAV_COMP_ID_CAMERA)
                        await gcs.video_start_streaming(222, mavutil.mavlink.MAV_COMP_ID_CAMERA2)
                        await asyncio.sleep(2)

                    raise With.Break

                    await asyncio.sleep(5)

                    event_new_cam = asyncio.Event()
                    cameras = []

                    async def find_cameras():
                        count = 0
                        while True:
                            ret = await gcs.wait_heartbeat(remote_mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, timeout=2)
                            if ret:
                                if ret not in cameras:
                                    cameras.append(ret)
                                    event_new_cam.set()
                                    print(f"Found new camera {ret = }")
                                else:
                                    # if no new cameras found in 3 seconds then break
                                    count += 1

                    async def atest1(comp):
                        ret = await gcs.wait_heartbeat(target_system=222, target_component=comp, timeout=1)
                        print(f"Heartbeat {comp} {ret = }")
                        ret = await gcs.image_start_capture(222, comp, interval=0.2, count=5)
                        print(f"Image Capture {comp = } {ret = }")
                        while True:
                            ret = await gcs.wait_for_message(mavlink.MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED, 222, comp, 2)
                            print(f"Image Request {comp = } {ret = }")
                            if not ret:
                                print(f"BREAK Image Request {comp = } {ret = }")
                                break
                            # await asyncio.sleep(1)
                        # await asyncio.sleep(5)

                    async def atest2(comp):
                        for i in range(10):
                            ret = await gcs.wait_heartbeat(target_system=222, target_component=comp, timeout=2)
                            print(f"Heartbeat {comp} {ret = }")

                    async def atest3(task):
                        await asyncio.sleep(3)

                        print(f"Cancelling {task = }")
                        task.cancel()

                        print(f"Cancelled {task = }")

                    # gcs.set_target(222, 22)
                    #
                    # msg = await gcs.request_camera_information(222, 22)
                    # print (f"request_camera_information {msg} {msg.get_msgId() = }")
                    print()
                    print()
                    for i in range(2):
                        gcs.video_start_streaming(222, 22)
                        time.sleep(1)
                        # gcs.request_storage_information(222, 22)
                        gcs.video_stop_streaming(222, 22)
                        time.sleep(1)
                    raise With.Break

                    await asyncio.sleep(11)
                    # gcs.request_camera_settings(222, 22)
                    #
                    # # capture 5 images from cameras 22 and 23
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
                        print(f"CancelledError {e = }")

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
                    # UAV_server.component[22].cameras.list_files()
                    # # # # gcs.image_start_capture(222, 23, interval=1, count=5)
                    # # #
                    # # #
                    # # # # Start & stop drone video capture
                    # gcs.video_start_capture(222, 22, frequency=1)
                    # time.sleep(2)
                    # gcs.video_stop_capture(222, 22)   # todo create new file on drone
                    # time.sleep(1)
                    # # #
                    # # UAV_server.component[22].cameras.list_files()
                    # # # Start & stop drone video streaming cameras 22
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
                    # UAV_server.component[22].cameras.list_files()
                    # gcs.video_start_streaming(222, 22)
                    # gcs.video_start_streaming(222, 22)
                    # time.sleep(2)
                    # # gcs.request_storage_information(222, 22)
                    # gcs.video_stop_streaming(222, 22)


if __name__ == '__main__':
    # UDP_ENCODER = 'rawvideo'  # 'h264'
    UDP_ENCODER = 'h264'
    num_cams = 1

    # #
    # p = Process(target=display, args=(2,UDP_ENCODER))
    # p.start()

    asyncio.run(main(num_cams, UDP_ENCODER))
    # p.terminate()
