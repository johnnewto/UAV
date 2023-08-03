#!/usr/bin/env python
"""
Gstreamer video capture
https://www.ardusub.com/developers/opencv.html
"""
import socket

import cv2
import gi
import numpy as np
from imutils import resize
from ping_ip import ping_ip
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import time

import paho.mqtt.client as mqtt

import time
# from dataloader import LoadImages, resize
from pathlib import Path
import gst_parameters as params

# dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_1000)
# # Initialize the detector parameters using default values
# parameters = cv2.aruco.DetectorParameters_create()


class Video():
    """
    """

    def __init__(self, gstcommand, address='127.0.0.1', port=5000, code_patch_size=100):
        """Summary
        Args:
            port (int, optional): UDP port
        """

        Gst.init(None)

        self.gstcommand = gstcommand
        self.address = address
        self.port = port
        self.code_patch_size = code_patch_size

        self.latest_frame = self._new_frame = None
        self.video_pipe = None
        self.video_sink = None
        self.pause = False
        self.run()



    def start_gst(self, config=None):
        """ Start gstreamer pipeline and sink

        """
        if not config:
            config = \
                [
                    'videotestsrc ! decodebin',
                    '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
                    '! appsink'
                ]
        # command = ' '.join(config)
        command = ' '.join(self.gstcommand)
        print(command)
        self.video_pipe = Gst.parse_launch(command)
        self.video_pipe.set_state(Gst.State.PLAYING)
        self.video_sink = self.video_pipe.get_by_name('appsink0')

    @staticmethod
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

    def frame(self):
        """ Get Frame
        Returns:
            np.ndarray: latest retrieved image frame
        """
        if self.frame_available:
            self.latest_frame = self._new_frame
            # reset to indicate latest frame has been 'consumed'
            self._new_frame = None
        return self.latest_frame

    def frame_available(self):
        """Check if a new frame is available
        Returns:
            bool: true if a new frame is available
        """
        return self._new_frame is not None

    def run(self):
        """ Get frame to update _new_frame
        """

        self.start_gst()
        try:
            self.video_sink.connect('new-sample', self.callback)
        except:
            pass

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        # if not self.pause:
        self._new_frame = self.gst_to_opencv(sample)

        return Gst.FlowReturn.OK


data_received = ''


def toggle_valve_state(pipeline, valvename):
    # Assuming you have a valve element named 'myvalve' in your pipeline
    valve = pipeline.get_by_name(valvename)
    current_drop_state = valve.get_property("drop")
    print("current_drop_state", current_drop_state)
    valve.set_property("drop", not current_drop_state)
    current_drop_state = valve.get_property("drop")
    print("new_drop_state", current_drop_state)

    # valve.set_property("drop", state)
def set_valve_state(pipeline, valvename, drop_state):
    # Assuming you have a valve element named 'myvalve' in your pipeline
    valve = pipeline.get_by_name(valvename)
    current_drop_state = valve.get_property("drop")
    print("current_drop_state", current_drop_state)
    valve.set_property("drop", drop_state)
    current_drop_state = valve.get_property("drop")
    print("new_drop_state", current_drop_state)




class Mqtt:
    def __init__(self, camera, video):
        self.camera = camera
        self.video = video
        self.client = mqtt.Client(self.camera)

        addr = "10.42.0.1"
        if ping_ip(addr):
            print("Connecting to ", addr)
            self.client.connect(addr)
        else:
            print("Connecting to ", "127.0.0.1")
            self.client.connect("127.0.0.1")

        self.client.loop_start()
        self.client.subscribe("STREAM-CAMERA")
        self.client.on_message = self.on_mqtt_message


    def on_mqtt_message(self, client, userdata, message):
        mess = str(message.payload.decode("utf-8"))
        print("Received message: ", mess)
        if mess == self.camera:
            set_valve_state(self.video.video_pipe, "myvalve", False)
        else:
            set_valve_state(self.video.video_pipe, "myvalve", True)

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("Closed mqtt client")


def main(camera="CAM-0"):

    cv2.namedWindow(camera, cv2.WINDOW_NORMAL)
    gstcommand = params.cameras[camera]["gst"]
    video = Video(gstcommand)
    mqtt = Mqtt(camera, video)

    print('Initialising stream...')
    waited = 0
    while not video.frame_available():
        waited += 1
        print('\r  Frame not available (x{})'.format(waited), end='')
        cv2.waitKey(30)

    print('\nSuccess!\nStarting streaming - press "q" to quit.')

    wait_time = 1
    count = 0
    while True:

        if video.frame_available() and count % 10 == 0:
            frame = video.frame().copy()
            # # cv2.putText(frame, f'{frame_num:2d} {data_received}', (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
            frame = resize(frame, width= 600)
            cv2.imshow(camera, frame)
            pass


        if count % 1000 == 0:
            print(data_received, count)
        count += 1


        k = cv2.waitKey(wait_time)

        if k == ord('q') or k == ord('Q') or k == 27:
            break

        if k == ord('v'):
            # Assuming you have a valve element named 'myvalve' in your pipeline
            valve = video.video_pipe.get_by_name("myvalve")
            current_drop_state = valve.get_property("drop")
            print("current_drop_state", current_drop_state)
            valve.set_property("drop", not current_drop_state)
            current_drop_state = valve.get_property("drop")
            print("new_drop_state", current_drop_state)

            time.sleep(2)

            # video.video_pipe.set_state(Gst.State.PLAYING)

        if k == ord(' '):
            if wait_time != 0:
                wait_time = 0
            else:
                wait_time = 1

        if k == ord('s'):
            save = 0
            save_path = Path(params.save_path) / data_received
            save_path.mkdir(exist_ok=True)
            pass

    mqtt.close()

"""
Test with :

from first terminal run 
    gst-launch-1.0 udpsrc port=5000 ! application/x-rtp,encoding-name=H264,payload=96 ! rtph264depay ! h264parse ! queue ! avdec_h264 ! xvimagesink sync=false async=false -e

from second terminal run 
    mosquitto_pub -m "CAM-0" -t "STREAM-CAMERA"
    mosquitto_pub -m "CAM-1" -t "STREAM-CAMERA"
"""

if __name__ == '__main__':
    from multiprocessing import Process
    cams = []
    for cam in list(params.cameras.keys())[:2]:
        print(cam)
        p = Process(target=main, args=(cam,))
        p.start()
        cams.append(p)

    for p in cams:
        p.join()