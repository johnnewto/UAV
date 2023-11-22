#!/bin/sh
echo "Display avdec_h265"

PORT=5010
# gst-launch-1.0 udpsrc port=${PORT} ! media=video, clock-rate=90000, encoding-name=H265, payload=96 ! rtph265depay ! h265parse ! avdec_h265 ! queue ! videoconvert ! autovideosink sync=false
#gst-launch-1.0 -vvv udpsrc port=${PORT} ! media=video, clock-rate=90000, encoding-name=H265, payload=96 ! rtph265depay ! decodebin ! autovideosink sync=false

gst-launch-1.0 udpsrc port=${PORT} caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H265, payload=(int)96" ! rtph265depay ! h265parse !  avdec_h265 ! videoconvert ! autovideosink sync=false
# GST_DEBUG=3 \
# gst-launch-1.0 udpsrc port=${PORT} caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H265, payload=(int)96" ! rtph265depay ! decodebin ! videoconvert ! autovideosink



