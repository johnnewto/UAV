#!/bin/sh
echo "USB camera display"

gst-launch-1.0  v4l2src device=/dev/video0 ! video/x-raw,format=YUY2,width=640,height=480,framerate=30/1 ! xvimagesink sync=false
#gst-launch-1.0 videotestsrc ! videoconvert ! video/x-raw,framerate=15/1,width=1280,height=720 !  x265enc bitrate=4000 tune=4 log-level=2 key-int-max=10   ! rtph265pay config-interval=5 ! udpsink host=192.168.144.10 port=${PORT}