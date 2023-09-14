#!/usr/bin/env python
"""
Gstreamer video capture
https://www.ardusub.com/developers/opencv.html
"""
import socket
import time

import cv2
import gi
import numpy as np


gi.require_version('Gst', '1.0')
from gi.repository import Gst


import datetime

from pathlib import Path


class FPS:
    def __init__(self):
        # store the start time, end time, and total number of frames
        # that were examined between the start and end intervals
        self._start = None
        self._end = None
        self._numFrames = 0

    def start(self):
        # start the timer
        self._start = datetime.datetime.now()
        return self

    def stop(self):
        # stop the timer
        self._end = datetime.datetime.now()

    def update(self):
        # increment the total number of frames examined during the
        # start and end intervals
        self._numFrames += 1

    def elapsed(self):
        # return the total number of seconds between the start and
        # end interval
        return (self._end - self._start).total_seconds()

    def fps(self):
        # compute the (approximate) frames per second
        return self._numFrames / self.elapsed()


# dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_1000)
# # Initialize the detector parameters using default values
# parameters = cv2.aruco.DetectorParameters_create()


class GST_Video():
    """BlueRov video capture class constructor

    Attributes:
        port (int): Video UDP port
        video_codec (string): Source h264 parser
        video_decode (string): Transform YUV (12bits) to BGR (24bits)
        video_pipe (object): GStreamer top-level pipeline
        video_sink (object): Gstreamer sink element
        video_sink_conf (string): Sink configuration
        video_source (string): Udp source ip and port
        latest_frame (np.ndarray): Latest retrieved video frame
    """

    def __init__(self, address='127.0.0.1', port=1234, code_patch_size=100):
        """Summary
        Args:
            port (int, optional): UDP port
        """

        Gst.init(None)

        self.address = address
        self.port = port
        self.code_patch_size = code_patch_size

        self.latest_frame = self._new_frame = None

        # [Software component diagram](https://www.ardusub.com/software/components.html)
        # UDP video stream (:5600)
        # self.video_source = f'udpsrc address={address} port={port}'
        self.video_source = f'rtspsrc location=rtsp://admin:admin@192.168.144.108:554 latency=100 ! queue'
        # self.video_codec = '! application/x-rtp, payload=96 ! rtph264depay ! h264parse ! avdec_h264'
        self.video_codec = '! rtph264depay ! h264parse ! avdec_h264'
        # Python don't have nibble, convert YUV nibbles (4-4-4) to OpenCV standard BGR bytes (8-8-8)
        self.video_decode = '! decodebin ! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert'
        # Create a sink to get data
        self.video_sink_conf = '! appsink emit-signals=true sync=false max-buffers=2 drop=true'

        self.video_pipe = None
        self.video_sink = None
        self.pause = False
        self.run()

    def start_gst(self, config=None):
        """ Start gstreamer pipeline and sink
        Pipeline description list e.g:
            [
                'videotestsrc ! decodebin', \
                '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
                '! appsink'
            ]

        Args:
            config (list, optional): Gstreamer pileline description list
        """

        if not config:
            config = \
                [
                    'videotestsrc ! decodebin',
                    '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
                    '! appsink'
                ]

        command = ' '.join(config)
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

        self.start_gst(
            [
                self.video_source,
                self.video_codec,
                self.video_decode,
                self.video_sink_conf
            ])

        self.video_sink.connect('new-sample', self.callback)

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        # if not self.pause:
        self._new_frame = self.gst_to_opencv(sample)

        return Gst.FlowReturn.OK


"""
Test with :

gst-launch-1.0 -v filesrc location=~/Videos/Big_Buck_Bunny_720_10s_2MB.mp4 ! decodebin ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=1234

gst-launch-1.0 -v filesrc location=~/Videos/paragliders-1.mp4 ! decodebin ! x264enc             ! rtph264pay ! udpsink host=127.0.0.1 port=1234
gst-launch-1.0 -v filesrc location=~/Videos/paragliders-1.mp4 ! decodebin ! x264enc bitrate=300 ! rtph264pay ! udpsink host=127.0.0.1 port=1234
 
gst-launch-1.0 -v videotestsrc ! x264enc             ! rtph264pay ! udpsink host=127.0.0.1 port=1235

gst-launch-1.0 -v videotestsrc ! x264enc bitrate=2048 ! rtph264pay ! udpsink host=127.0.0.1 port=1235
gst-launch-1.0 -v videotestsrc ! video/x-raw,format=BGR,width=640,height=480 ! x264enc bitrate=2048! rtph264pay ! udpsink host=127.0.0.1 port=1235
experimental:
#    out = cv2.VideoWriter('appsrc ! videoconvert ! x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast ! rtph264pay config-interval=1 pt=96 ! udpsink host=127.0.0.1 port=5000',
# 
#    format=BGR,width=640,height=480,framerate=20/1
#    gst_str_rtp = "appsrc ! queue ! videoconvert ! video/x-raw ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=1234"
# 
#    appsrc name=source is-live=true block=true format=GST_FORMAT_TIME " \
#                     " caps=video/x-raw,format=BGR,width=640,height=480,framerate={}/1 " \
#                     "! videoconvert ! video/x-raw,format=I420 "
# 
#                     video/x-raw,format=BGR,width=640,height=480,framerate={}/1
# 
# gst-launch-1.0 -v videotestsrc ! video/x-raw,format=BGR,width=640,height=480 ! x264enc bitrate=2048! rtph264pay ! udpsink host=127.0.0.1 port=1234
# gst-launch-1.0 -v videotestsrc ! x264enc format=BGR,width=640,height=480 ! rtph264pay ! udpsink host=127.0.0.1 port=1234
"""

if __name__ == '__main__':
    cv2.namedWindow('Receive', cv2.WINDOW_NORMAL)

    video = GST_Video()
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

    cv2.destroyAllWindows()