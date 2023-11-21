#!/bin/sh
echo "Display avdec_h265"

PORT=5000
# gst-launch-1.0 udpsrc port=${PORT} ! rtph265depay ! h265parse ! avdec_h265 ! queue ! videoconvert ! autovideosink sync=false
gst-launch-1.0 -vvv udpsrc port=${PORT} ! application/x-rtp,encoding-name=H265 ! rtph265depay ! decodebin ! autovideosink sync=false
