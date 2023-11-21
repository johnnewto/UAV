#!/bin/sh
echo "Foward rtsp to UDPsink IP PORT"

# foward to UDPsink IP PORT
# IP=127.0.0.1
# IP=10.42.0.1
IP=192.168.1.175
PORT=5010
gst-launch-1.0 rtspsrc location="rtsp://admin:admin@192.168.144.108:554" latency=100 ! queue ! rtph265depay ! rtph265pay config-interval=1 ! udpsink host=${IP} port=${PORT} sync=false async=false





