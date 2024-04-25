#!/bin/bash

# from https://gist.github.com/hum4n0id/cda96fb07a34300cdb2c0e314c14df0a

gst-launch-1.0 -v videotestsrc ! 'video/x-raw,format=RGB,width=1920, height=1080, framerate=30/1' ! nvvidconv flip-method=2 ! \
nvv4l2h264enc insert-sps-pps=true bitrate=16000000 ! rtph264pay ! udpsink host=127.0.0.1 port=5000

# gst-launch-1.0 filesrc location=paragliders.mp4 ! decodebin ! videoconvert ! autovideosink 
# gst-launch-1.0 -v videotestsrc \
#   ! x264enc 

# gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM),width=1920, height=1080, framerate=30/1, format=NV12' ! nvvidconv flip-method=2 ! nvv4l2h264enc insert-sps-pps=true bitrate=16000000 ! rtph264pay ! udpsink port=5000 host=$HOST

# gst-launch-1.0 filesrc location=paragliders.mp4 \
#   ! qtdemux ! fakesink
#   ! decodebin ! videoconvert \
#   ! fakesink
#    ! videoscale ! autovideosink

# gst-launch-1.0 filesrc location=$PATH_TO_FILE ! avidemux ! h264parse ! omxh264dec ! nvvidconv ! queue ! 'video/x-raw,width=640,height=480' 
#! nvstabilize crop-margin=0.1 queue-size=5 ! 'video/x-raw,width=320,height=240' ! nveglglessink sync=false