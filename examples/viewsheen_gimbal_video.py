#!/usr/bin/env python
"""
viewsheen_sdk gimbal control

"""
import asyncio
import socket
import time

import cv2
import numpy as np

# from UAV.camera_sdks.viewsheen import GST_Video
import gstreamer.utils as gst_utils
from UAV import MAVCom
from UAV.mavlink import mavlink
from UAV.camera_sdks.viewsheen.gimbal_cntrl import VS_IP_ADDRESS, VS_PORT, KeyReleaseThread
from UAV.mavlink.vs_gimbal import GimbalClient, GimbalServer
from gstreamer import GstVideoSource

# self.video_source = f'rtspsrc location=rtsp://admin:admin@192.168.144.108:554 latency=100 ! queue'
# # self.video_codec = '! application/x-rtp, payload=96 ! rtph264depay ! h264parse ! avdec_h264'
# self.video_codec = '! rtph264depay ! h264parse ! avdec_h264'
# # Python don't have nibble, convert YUV nibbles (4-4-4) to OpenCV standard BGR bytes (8-8-8)
# self.video_decode = '! decodebin ! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert'
# # Create a sink to get data
# self.video_sink_conf = '! appsink emit-signals=true sync=false max-buffers=2 drop=true'

DEFAULT_PIPELINE = gst_utils.to_gst_string([
            'rtspsrc location=rtsp://admin:admin@192.168.144.108:554 latency=100 ! queue',
            'rtph264depay ! h264parse ! avdec_h264',
            'decodebin ! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
            'appsink name=mysink emit-signals=true sync=false async=false max-buffers=2 drop=true',
            # # 'x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast',
            # 'x264enc tune=zerolatency',
            # 'rtph264pay ! udpsink host=127.0.0.1 port=5000',
            # 't.',
            # 'queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=5/1,format=(string)BGR',
            # 'videoconvert ! appsink name=mysink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
        ])


def gst_to_opencv(sample):
    """Transform byte array into np array
    Args:q
        sample (TYPE): Description
    Returns:
        TYPE: Description
    """
    buf = sample.get_buffer()
    caps_structure = sample.get_caps().get_structure(0)
    array = np.ndarray(
        (
            caps_structure.get_value('height'),
            caps_structure.get_value('width'),
            3
        ),
        buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
    return array

async def main(sock=None):


    cv2.namedWindow('Receive', cv2.WINDOW_NORMAL)

    # video = GST_Video.GST_Video()


    MAV_TYPE_GCS = mavlink.MAV_TYPE_GCS
    MAV_TYPE_CAMERA = mavlink.MAV_TYPE_CAMERA
    MAV_TYPE_GIMBAL = mavlink.MAV_TYPE_GIMBAL

    con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
    # con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"
    with MAVCom(con1, source_system=111) as client:
        with MAVCom(con2, source_system=222, ) as server:
            gimbal:GimbalClient = client.add_component(GimbalClient(mav_type=MAV_TYPE_GCS, source_component=11, loglevel=10))
            server.add_component(GimbalServer(mav_type=MAV_TYPE_GIMBAL, source_component=22, loglevel=10))

            ret = await gimbal.wait_heartbeat(target_system=222, target_component=22, timeout=1)
            print(f"Heartbeat {ret = }")

            time.sleep(0.1)
            gimbal.set_target(222, 22)

            NAN = float("nan")

            print('Initialising stream...')
            waited = 0
            pipeline = GstVideoSource(DEFAULT_PIPELINE, leaky=True)
            pipeline.startup()

            while True:
                buffer = pipeline.pop()
                if buffer:
                    break
                waited += 1
                print('\r  Frame not available (x{})'.format(waited), end='')
                cv2.waitKey(30)

            print('\nSuccess!\nStarting streaming - press "q" to quit.')
            # ret, (width, height) = gst_utils.get_buffer_size_from_gst_caps(Gst.Caps)

            gimbal_speed = 40
            while True:
                buffer = pipeline.pop()
                if buffer:
                    cv2.imshow('Receive', buffer.data)

                k = cv2.waitKey(1)
                if k == ord('q') or k == ord('Q') or k == 27:
                    break

                if k == ord('d'):  # Right arrow key
                    print("Right arrow key pressed")
                    await gimbal.set_attitude(NAN, NAN, 0.0, 0.2)
                    # pan_tilt(gimbal_speed)
                    KeyReleaseThread().start()

                if k == ord('a'):  # Left arrow key
                    print("Left arrow key pressed")
                    await gimbal.set_attitude(NAN, NAN, 0.0, -0.2)
                    KeyReleaseThread().start()

                if k == ord('w'):
                    print("Up arrow key pressed")
                    await gimbal.set_attitude(NAN, NAN, 0.2, 0.0)
                    KeyReleaseThread().start()

                if k == ord('s'):
                    print("Down arrow key pressed")
                    await gimbal.set_attitude(NAN, NAN, -0.2, 0.0)
                    KeyReleaseThread().start()

                if k == ord('1'):
                    print("Zoom in pressed")
                    await gimbal.set_zoom(1)

                if k == ord('2'):
                    print("Zoom out pressed")
                    await gimbal.set_zoom(2)

                if k == ord('3'):
                    print("Zoom stop pressed")
                    await gimbal.set_zoom(3)

                if k == ord('4'):
                    print("Zoom  = 1")
                    await gimbal.set_zoom(4)

                if k == ord('5'):
                    print("Zoom x2 in")
                    await gimbal.set_zoom(5)


                if k == ord('6'):
                    print("Zoom x2 out")
                    await gimbal.set_zoom(6)

                if k == ord('c'):
                    print("Snapshot in pressed")
                    gimbal.start_capture()

        pipeline.shutdown()

if __name__ == '__main__':


    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect to viewsheen_sdk gimbal
    sock.connect((VS_IP_ADDRESS, VS_PORT))

    asyncio.run(main(sock))
    sock.close()
    cv2.destroyAllWindows()