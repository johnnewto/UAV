#!/bin/sh
echo "Take pictures"
CAM=1
IP=127.0.0.1
PORT=5000
FPS=5
GST_DEBUG=4 \ 
# gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=40 ! 'video/x-raw(memory:NVMM), format=NV12, width=3840, height=2160, framerate=21/1' ! nvvidconv ! video/x-raw,format=RGBA ! multifilesink location=test1.rgba max-files=1
# gst-launch-1.0 nvarguscamerasrc sensor_id="${CAM}"  ! 'video/x-raw(memory:NVMM),width=4032,height=3040,framerate=30/1' \
# ! videorate max-rate="${FPS}" drop-only=true ! queue max-size-buffers=3 leaky=downstream \

# gst-launch-1.0 filesrc location=test1.rgba ! videoparse format=rgba width=3840 height=2160 framerate=0/1 ! pngenc ! filesink location=test1.png


https://stackoverflow.com/questions/70001643/how-to-capture-a-raw-image-png-using-a-nvargus-camera-in-gstreamer