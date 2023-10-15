import time

from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil, mavlink
from UAV.utils.general import boot_time_str, With, read_camera_dict_from_toml

from UAV.camera import GSTCamera, AirsimCamera
from gstreamer import GstPipeline, Gst, GstContext, GstPipes
from gstreamer.utils import to_gst_string
from pathlib import Path
import cv2
DISPLAY_H264_PIPELINE = to_gst_string([
    'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
    'queue ! rtph264depay !  avdec_h264',
    'videoconvert',
    'fpsdisplaysink ',
])

DISPLAY_RAW_PIPELINE = to_gst_string([
    'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB,depth=(string)8, width=(string)640, height=(string)480, payload=(int)96',
    'queue ! rtpvrawdepay ! videoconvert',
    'fpsdisplaysink sync=false ',
])
DISPLAY_RAW_PIPELINE = to_gst_string([
    # 'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB,depth=(string)8, width=(string)640, height=(string)480, payload=(int)96',
    # 'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB,depth=(string)8, width=(string)640, height=(string)480',
    'udpsrc port=5000 caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB, depth=(string)8, width=(string)1920, height=(string)1080"',
    'queue ! rtpvrawdepay',

    'videorate',
    'video/x-raw,framerate=10/1',
    'videoconvert',
    'fpsdisplaysink sync=false ',
])
if __name__ == '__main__':
    # udp_encoder = 'h264'
    udp_encoder = 'rawvideo'
    display_pipeline = DISPLAY_RAW_PIPELINE if 'raw' in udp_encoder else DISPLAY_H264_PIPELINE
    print (f"{boot_time_str =}")
    config_path = Path("../config")
    with GstContext():
        with GstPipeline(display_pipeline) as disp_pipeline:
            with  AirsimCamera(camera_dict=read_camera_dict_from_toml(config_path / "airsim_camera_info.toml"), udp_encoder=udp_encoder, loglevel=20).open() as air_cam:
                # air_cam.image_start_capture(0.1, 5)
                # # time.sleep(2)
                # while air_cam._gst_image_save.is_active:
                #     time.sleep(0.1)
                time.sleep(5)
                air_cam.video_start_streaming()
                time.sleep(10)
                air_cam.video_stop_streaming()
                time.sleep(1)
                print (f"Waiting for capture thread to finish")



    # with GstContext():
    #     with  AirsimCamera(camera_dict=read_camera_dict_from_toml(config_path / "airsim_camera_info.toml"), loglevel=10) as cam_fake1
    #     # with  GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"), loglevel=10) as cam_fake1:
    #         cam_fake1.image_start_capture(0.1, 5)
    #         while cam_fake1._gst_image_save.is_active:
    #             if cam_fake1.last_image is not None:
    #                 pass
    #                 # cv2.imshow('image', cam_fake1.last_image)
    #                 # cam_fake1.last_image = None
    #             cv2.waitKey(10)
    #         print (f"Waiting for capture thread to finish")


