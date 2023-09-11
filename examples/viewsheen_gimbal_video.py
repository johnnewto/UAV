#!/usr/bin/env python
"""
viewsheen_sdk gimbal control

"""

import cv2

from viewsheen_sdk.gimbal_cntrl import pan_tilt, snapshot,  zoom, VS_IP_ADDRESS, VS_PORT, KeyReleaseThread
import socket
from viewsheen_sdk import GST_Video
import time
import datetime

from pathlib import Path

from UAV.mavlink.vs_gimbal import GimbalClient, GimbalServer, mavutil, MAVCom

def main(sock=None):


    cv2.namedWindow('Receive', cv2.WINDOW_NORMAL)

    video = GST_Video.GST_Video()

    MAV_TYPE_GCS = mavutil.mavlink.MAV_TYPE_GCS
    MAV_TYPE_CAMERA = mavutil.mavlink.MAV_TYPE_CAMERA
    MAV_TYPE_GIMBAL = mavutil.mavlink.MAV_TYPE_GIMBAL

    con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
    con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"
    with MAVCom(con1, source_system=111, debug=False) as client:
        with MAVCom(con2, source_system=222, debug=False) as server:
            gimbal: GimbalClient = client.add_component(
                GimbalClient(client, mav_type=MAV_TYPE_GCS, source_component=11, debug=False))
            server.add_component(GimbalServer(server, mav_type=MAV_TYPE_GIMBAL, source_component=22, debug=False))
            server.add_component(GimbalServer(server, mav_type=MAV_TYPE_CAMERA, source_component=23, debug=False))


            gimbal.wait_heartbeat(target_system=222, target_component=22, timeout=0.99)
            time.sleep(0.1)
            gimbal.set_target(222, 22)

            NAN = float("nan")

            print('Initialising stream...')
            waited = 0
            while not video.frame_available():
                waited += 1
                print('\r  Frame not available (x{})'.format(waited), end='')
                cv2.waitKey(30)

            print('\nSuccess!\nStarting streaming - press "q" to quit.')

            gimbal_speed = 40
            while True:

                if video.frame_available():
                    frame = video.frame().copy()
                    cv2.imshow('Receive', frame)

                k = cv2.waitKey(1)
                if k == ord('q') or k == ord('Q') or k == 27:
                    break

                if k == ord('d'):  # Right arrow key
                    print("Right arrow key pressed")
                    gimbal.set_attitude(NAN, NAN, 0.0, 0.2)
                    # pan_tilt(gimbal_speed)
                    KeyReleaseThread().start()

                if k == ord('a'):  # Left arrow key
                    print("Left arrow key pressed")
                    gimbal.set_attitude(NAN, NAN, 0.0, -0.2)
                    KeyReleaseThread().start()

                if k == ord('w'):
                    print("Up arrow key pressed")
                    gimbal.set_attitude(NAN, NAN, 0.2, 0.0)
                    KeyReleaseThread().start()

                if k == ord('s'):
                    print("Down arrow key pressed")
                    gimbal.set_attitude(NAN, NAN, -0.2, 0.0)
                    KeyReleaseThread().start()

                if k == ord('1'):
                    print("Zoom in pressed")
                    gimbal.set_zoom(1)

                if k == ord('2'):
                    print("Zoom out pressed")
                    gimbal.set_zoom(2)

                if k == ord('3'):
                    print("Zoom stop pressed")
                    gimbal.set_zoom(3)

                if k == ord('4'):
                    print("Zoom  = 1")
                    gimbal.set_zoom(4)

                if k == ord('5'):
                    print("Zoom x2 in")
                    gimbal.set_zoom(5)


                if k == ord('6'):
                    print("Zoom x2 out")
                    gimbal.set_zoom(6)

                if k == ord('c'):
                    print("Snapshot in pressed")
                    gimbal.start_capture()



if __name__ == '__main__':


    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect to viewsheen_sdk gimbal
    sock.connect((VS_IP_ADDRESS, VS_PORT))

    main(sock)
    sock.close()
    cv2.destroyAllWindows()