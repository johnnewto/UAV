#!/bin/sh
echo "Display avdec_h264"
PORT=5000
#PORT=554
#gst-launch-1.0 udpsrc port=5600 caps='application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264' ! rtph264depay ! avdec_h264 ! autovideosink sync=false
gst-launch-1.0 udpsrc port=${PORT} caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" \
! rtph264depay ! queue ! nvvidconv ! avdec_h264 ! videoconvert ! autovideosink
