#!/bin/sh
echo "Display rtsp"
IP=127.0.0.1
PORT=5000

# display
gst-launch-1.0 rtspsrc location="rtsp://admin:admin@192.168.144.108:554" latency=100 ! queue ! rtph265depay ! h265parse ! avdec_h265 ! autovideosink

# save to file
#gst-launch-1.0 -ev  rtspsrc location="rtsp://admin:admin@192.168.144.108:554/cam/realmonitor?channel=1&subtype=0" ! application/x-rtp, media=video, encoding-name=H264  ! queue ! rtph264depay ! h264parse ! matroskamux ! filesink location=received_h264.mkv

# foward to UDPsink
#gst-launch-1.0 rtspsrc location="rtsp://admin:admin@192.168.144.108:554" latency=100 ! queue ! rtph265depay ! rtph265pay config-interval=1 ! udpsink host=${IP} port=${PORT} sync=false async=false