import asyncio
import time

import gstreamer.utils as gst_utils
from gstreamer import GstPipeline, Gst, GstContext, GstPipes
from gstreamer.utils import to_gst_string

from UAV.cameras.gst_cam import GSTCamera
from UAV.logging import LogLevels
from UAV.mavlink import CameraClient, CameraServer, MAVCom, mavlink
from UAV.utils.general import boot_time_str, toml_load, config_dir

DISPLAY_H264_PIPELINE = to_gst_string([
    'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
    'queue ! rtph264depay ! avdec_h264',
    'videoconvert',
    'fpsdisplaysink ',
])


# con1 = "udpin:localhost:14445"
# con2 = "udpin:localhost:14445"
con1 = "udpin:192.168.144.1:14445"
con2 = "udpout:192.168.144.1:14445"
gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)


# if __name__ == '__main__':
async def main(num_cams):
    # logger.disabled = True
    print(f"{boot_time_str =}")
    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread

        display_pipelines = [GstPipeline(DISPLAY_H264_PIPELINE.format(5000 + i)) for i in range(num_cams)]
        with GstPipes(display_pipelines, loglevel=LogLevels.INFO):  # this will show the video on fpsdisplaysink
            with MAVCom(con1, source_system=111, loglevel=LogLevels.CRITICAL) as GCS_client:  # This normally runs on GCS
                with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server:  # This normally runs on drone
                    # add GCS manager
                    gcs: CameraClient = GCS_client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=LogLevels.DEBUG))
                    # add UAV cameras, This normally runs on drone
                    cam_1 = GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_0.toml"), loglevel=LogLevels.INFO)

                    UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_1, loglevel=10))

                    ret = await gcs.wait_heartbeat(target_system=222, target_component=mavlink.MAV_COMP_ID_CAMERA, timeout=2)
                    print(f"Heartbeat {ret = }")
                    await asyncio.sleep(0.1)
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


if __name__ == '__main__':
    # UDP_ENCODER = 'rawvideo'  # 'h264'
    UDP_ENCODER = 'h264'
    num_cams = 1


    asyncio.run(main(num_cams))
    # p.terminate()
