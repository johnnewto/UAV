#!/bin/bash

# from https://gist.github.com/hum4n0id/cda96fb07a34300cdb2c0e314c14df0a
# fps
gst-launch-1.0 -v udpsrc port=5000 ! "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" \
! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! fpsdisplaysink text-overlay=true sync=false


