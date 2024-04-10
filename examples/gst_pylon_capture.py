import numpy as np
import time
import cv2

from gstreamer import GstVideoSource, GstVideo, Gst, GLib, GstContext

WIDTH, HEIGHT, CHANNELS = 640, 480, 3
NUM_BUFFERS = 50
VIDEO_FORMAT = GstVideo.VideoFormat.RGB

video_format_str = GstVideo.VideoFormat.to_string(VIDEO_FORMAT)
# caps_filter = "capsfilter caps=video/x-raw,format={video_format_str},width={WIDTH},height={HEIGHT}".format(**locals())
caps_filter = "video/x-raw,format=BGR"
# command = "pylonsrc capture-error=skip  num-buffers={NUM_BUFFERS} ! {caps_filter} ! appsink emit-signals=True sync=false".format(**locals())
command = "pylonsrc capture-error=skip  ! {caps_filter} ! appsink emit-signals=True sync=false".format(**locals())

# 'pylonsrc capture-error=skip ! queue ! videoconvert ! autovideosink'

last_buffer = None
# with GstContext():
with GstVideoSource(command) as pipeline:
    cv2.namedWindow('camera', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('camera', int(600 * 1.5), int(480 * 1.5))
    while pipeline.is_active or pipeline.queue_size > 0:
        buffer = pipeline.pop()
        if buffer:
            print(f"{buffer.data.shape}")
            im = buffer.data
            cv2.imshow('camera', im)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

