import logging
LOGGING_LEVEL = logging.INFO

camera_dev = "CAM-0"
cameras = {
    "CAM-0": {
        "gst": [
            'videotestsrc pattern=smpte is-live=true ! tee name=t ',
            't. ! queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=10/1,format=(string)BGR ! videoconvert ! appsink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
            't. ! queue leaky=2 ! valve name=myvalve drop=true ! video/x-raw,format=I420,width=640,height=480 ! videoconvert ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=5000',
            ],
        "udp": True,
        "host": "127.0.0.1",
        "port": 5000,
    },
    "CAM-1": {
        "gst": [
            'videotestsrc pattern=ball is-live=true ! tee name=t ',
            't. ! queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=10/1,format=(string)BGR ! videoconvert ! appsink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
            't. ! queue leaky=2 ! valve name=myvalve drop=true ! video/x-raw,format=I420,width=640,height=480 ! videoconvert ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=5000',
            ],
        "udp": True,
        "host": "127.0.0.1",
        "port": 5000,
    },
    "CAM-2": {
        "gst": [
            'videotestsrc pattern=snow is-live=true ! tee name=t ',
            't. ! queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=10/1,format=(string)BGR ! videoconvert ! appsink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
            't. ! queue leaky=2 ! valve name=myvalve drop=true ! video/x-raw,format=I420,width=640,height=480 ! videoconvert ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=5000',
            ],
        "udp": True,
        "host": "127.0.0.1",
        "port": 5000,
    },
    "CAM-3": {
        "gst": [
            'videotestsrc pattern=pinwheel is-live=true ! tee name=t ',
            't. ! queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=10/1,format=(string)BGR ! videoconvert ! appsink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
            't. ! queue leaky=2 ! valve name=myvalve drop=true ! video/x-raw,format=I420,width=640,height=480 ! videoconvert ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=5000',
            ],
        "udp": True,
        "host": "127.0.0.1",
        "port": 5000,
        },

   }

# socket address and port
mqqt_address='127.0.0.1'
src_port=1234


