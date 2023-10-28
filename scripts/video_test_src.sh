#!/bin/sh
echo "Starting video test source "
echo " Cant get this to work????"

#gst-launch-1.0 videotestsrc ! videoconvert ! video/x-raw,framerate=60/1,width=1280,height=720 !  x264enc bitrate=4000   ! rtph264pay  ! udpsink host=localhost port=5600
#gst-launch-1.0 -e videotestsrc ! video/x-raw, width=640, height=480, framerate =30/1 ! x264enc ! rtph264pay ! udpsink host=localhost port=5600
GST_DEBUG=3 gst-launch-1.0 videotestsrc ! decodebin ! x264enc ! rtph264pay ! udpsink port=5000