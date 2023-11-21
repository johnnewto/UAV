#!/bin/sh
echo "Display rtsp"


# display
gst-launch-1.0 rtspsrc location="rtsp://admin:admin@192.168.144.108:554" latency=100 ! queue ! rtph265depay ! h265parse ! avdec_h265 ! autovideosink

# save to file
#gst-launch-1.0 -ev  rtspsrc location="rtsp://admin:admin@192.168.144.108:554/cam/realmonitor?channel=1&subtype=0" ! application/x-rtp, media=video, encoding-name=H264  ! queue ! rtph264depay ! h264parse ! matroskamux ! filesink location=received_h264.mkv





