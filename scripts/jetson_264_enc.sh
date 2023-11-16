#!/bin/sh
echo "Jetson nvv4l2h264enc "
CAM=1
IP=127.0.0.1
PORT=5000
FPS=30
GST_DEBUG=3 \
gst-launch-1.0 nvarguscamerasrc ! "video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1" \
! nvvidconv flip-method=2 \
! nvv4l2h264enc insert-sps-pps=true bitrate=4000000 \
! rtph264pay ! udpsink host=127.0.0.1 port=5000 sync=true

# ! videorate max-rate=60 drop-only=true ! queue max-size-buffers=3 leaky=downstream \
# ! interpipesink name=cam_0 
# ! nvv4l2h265enc bitrate=2000000 iframeinterval=300 vbv-size=33333 insert-sps-pps=true \
# control-rate=constant_bitrate profile=Main num-B-Frames=0 ratecontrol-enable=true preset-level=UltraFastPreset EnableTwopassCBR=false maxperf-enable=true \
# ! interpipesink name=cam_0 
# ! h265parse ! mpegtsmux alignment=7 ! queue ! udpsink clients="${IP}:${PORT}"

# gst-launch-1.0 nvarguscamerasrc sensor_id="${CAM}"  ! 'video/x-raw(memory:NVMM),width=4032,height=3040,framerate=30/1' ! nvoverlaysink
# 'nvv4l2h264enc num-B-Frames=2 vbv-size=420000 control-rate=1 bitrate={bitrate} profile=2 preset-level=2 insert-sps-pps=true maxperf-enable=1 insert-vui=true insert-aud=true idrinterval=15',
