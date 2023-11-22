#!/bin/sh
echo "Local x265enc "
CAM=1
IP=127.0.0.1
PORT=5010
FPS=10
BITRATE=2000


#gst-launch-1.0 nvarguscamerasrc  sensor_id=1 ! 'video/x-raw, width=4032, height=3040, format=NV12, framerate=30/1' \
#! videorate max-rate=${FPS} drop-only=true ! queue max-size-buffers=3 leaky=downstream \
#! tee name=t \
#t. ! queue ! videoconvert ! "video/x-raw(memory:NVMM), width=(int)2000, height=(int)1500, format=(string)NV12" \
#! x265enc bitrate=${BITRATE} ! rtph265pay config-interval=1 ! udpsink host=${IP} port=${PORT} sync=false async=false \
#t. ! queue ! xvimagesink
#

x265enc does not seem to work ...
gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw,format=YUY2,width=640,height=480,framerate=30/1 \
! videoconvert ! "video/x-raw, width=640, height=480, format=NV12" !  videoconvert  ! x265enc bitrate=4000 tune=4 log-level=2 key-int-max=10   ! rtph265pay config-interval=5 ! udpsink host=192.168.144.10 port=${PORT}


#gst-launch-1.0 videotestsrc ! videoconvert ! video/x-raw,framerate=15/1,width=1280,height=720 \
#!  x265enc bitrate=4000 tune=4 log-level=2 key-int-max=10   ! rtph265pay config-interval=5 ! udpsink host=192.168.144.10 port=${PORT}