#!/bin/sh
echo "Starting jetson test source "
CAM=1
IP=127.0.0.1
PORT=5000
FPS=30
GST_DEBUG=4 \ 
gst-launch-1.0 nvarguscamerasrc sensor_id="${CAM}"  ! 'video/x-raw(memory:NVMM),width=4032,height=3040,framerate=30/1' ! nvoverlaysink