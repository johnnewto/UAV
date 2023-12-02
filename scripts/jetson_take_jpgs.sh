#!/bin/sh
echo "Take pictures"
CAM=0
FPS=1
gst-launch-1.0 nvarguscamerasrc sensor_id="${CAM}"  ! 'video/x-raw(memory:NVMM),width=4032,height=3040,framerate=30/1' \
! videorate max-rate="${FPS}" drop-only=true ! queue max-size-buffers=3 leaky=downstream \
! nvvidconv ! 'video/x-raw(memory:NVMM), format=I420' ! nvjpegenc quality=95 idct-method=1 ! multifilesink location=test_%03d.jpg max-files=15
