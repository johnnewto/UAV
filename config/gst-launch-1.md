#### gst-launch-1.0 examples 
```bash
gst-launch-1.0   udpsrc port=5000 ! application/x-rtp, media=video, clock-rate=90000, encoding-name=H265, payload=96 ! queue ! rtph265depay ! avdec_h265 ! videoconvert ! capsfilter caps=video/x-raw,format=BGR  ! fpddisplaysink sync=false

gst-launch-1.0   udpsrc port=5000 ! application/x-rtp, media=video, clock-rate=90000, encoding-name=H264, payload=96 ! queue ! rtph264depay ! avdec_h264 ! videoconvert ! capsfilter caps=video/x-raw,format=BGR  ! fpsdisplaysink sync=false

```