#!/bin/sh
echo "Jetson nvv4l2h265enc "
CAM=1
IP=10.42.0.1
PORT=5000
FPS=10
BITRATE=2000000

# GST_DEBUG=3 \
# gst-launch-1.0 nvarguscamerasrc sensor_id="${CAM}" ! "video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1" \
# ! videorate max-rate=60 drop-only=true ! queue max-size-buffers=3 leaky=downstream \
# ! nvvidconv flip-method=2 \
# ! nvv4l2h265enc bitrate=2000000 iframeinterval=300 vbv-size=33333 insert-sps-pps=true \
# control-rate=constant_bitrate profile=Main num-B-Frames=0 ratecontrol-enable=true \
# preset-level=UltraFastPreset EnableTwopassCBR=false maxperf-enable=true \
# ! rtph265pay config-interval=1 ! udpsink host="10.42.0.1" port=5000 sync=true

# ! videorate max-rate=60 drop-only=true ! queue max-size-buffers=3 leaky=downstream \
# ! interpipesink name=cam_0 
# ! interpipesink name=cam_0 
# ! h265parse ! mpegtsmux alignment=7 ! queue ! udpsink clients="${IP}:${PORT}"

# gst-launch-1.0 nvarguscamerasrc sensor_id="${CAM}"  ! 'video/x-raw(memory:NVMM),width=4032,height=3040,framerate=30/1' ! nvoverlaysink
# 'nvv4l2h264enc num-B-Frames=2 vbv-size=420000 control-rate=1 bitrate={bitrate} profile=2 preset-level=2 insert-sps-pps=true maxperf-enable=1 insert-vui=true insert-aud=true idrinterval=15',
GST_DEBUG=4 \ 
gst-launch-1.0 nvarguscamerasrc  sensor_id=1 ! 'video/x-raw(memory:NVMM), width=4032, height=3040, format=NV12, framerate=30/1' \
! videorate max-rate=${FPS} drop-only=true ! queue max-size-buffers=3 leaky=downstream \
! tee name=t \
t. ! queue ! nvvidconv ! "video/x-raw(memory:NVMM), width=(int)2000, height=(int)1500, format=(string)NV12" \
! nvv4l2h265enc bitrate=${BITRATE} ! rtph265pay config-interval=1 ! udpsink host=${IP} port=${PORT} sync=false async=false \
t. ! queue ! nvoverlaysink

# gst-launch-1.0 -e nvarguscamerasrc  sensor_id=1 ! 'video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12, framerate=30/1' \
# ! videorate max-rate=${FPS} drop-only=true ! queue max-size-buffers=3 leaky=downstream ! tee name=t \
# t. queue ! nvv4l2h265enc bitrate=${BITRATE} ! rtph265pay config-interval=1 ! udpsink host=${IP} port=${PORT} sync=false async=false \
# t. queue ! nvoverlaysink

# ! nvvidconv ! "video/x-raw(memory:NVMM), width=(int)1920, height=(int)1080, format=(string)I420"