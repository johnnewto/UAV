#!/bin/bash

# from https://gist.github.com/hum4n0id/cda96fb07a34300cdb2c0e314c14df0a

# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/etc/alternatives/deepstream-plugins
gst-launch-1.0 -v pylonsrc !  'video/x-raw,format=YUY2' ! nvvidconv flip-method=2 ! \
nvv4l2h264enc insert-sps-pps=true bitrate=16000000 ! rtph264pay ! udpsink host=127.0.0.1 port=5000

# gst-launch-1.0 -v pylonsrc !  'video/x-bayer,format=rggb' ! bayer2rgb ! nvvidconv flip-method=2 ! \
# nvv4l2h264enc insert-sps-pps=true bitrate=16000000 ! rtph264pay ! udpsink host=127.0.0.1 port=5000


# gst-launch-1.0 -v pylonsrc !  'video/x-bayer,format=rggb,width=1920,height=1080' ! bayer2rgb ! nvvidconv flip-method=2 ! \
# nvv4l2h264enc insert-sps-pps=true bitrate=16000000 ! rtph264pay ! udpsink host=127.0.0.1 port=5000

# # gst-launch-1.0 pylonsrc ! videoconvert ! fpsdisplaysink
# gst-launch-1.0 -v pylonsrc !  'video/x-raw(memory:NVMM),format=RGB,width=1920,height=1080' ! nvvidconv flip-method=2 ! \
# nvv4l2h264enc insert-sps-pps=true bitrate=16000000 ! rtph264pay ! udpsink host=127.0.0.1 port=5000