
from gstreamer import GstPipeline, GstContext, GstStreamUDP
from gstreamer.utils import *
import time

command1 = to_gst_string(['videotestsrc pattern=ball ! video/x-raw,width=640,height=480,framerate=10/1 ! tee name=t allow-not-linked=true',

                        "t.",
                        'queue max-size-buffers=5 ! intervideosink channel=channel_0  ',

                        "t.",
                        'queue max-size-buffers=5 ! intervideosink channel=channel_1 ',

                        "t.",
                        'queue ! autovideosink',

                        "t.",
                        'queue ! fakesink',
                        ])


# _command1 = to_gst_string(['videotestsrc pattern=ball',
#                                     'intervideosink channel=video-capture-channel  '])
#
#
# command2 = to_gst_string(['intervideosrc channel=video-capture-channel  ',
#                                     'videoconvert',
#                                     # 'autovideosink',
#                                     'x264enc',
#                                     'mp4mux ! filesink location=file1.mp4',
#                                     ])
# command3 = to_gst_string(['intervideosrc channel=video-capture-channel  ',
#                                     'videoconvert',
#                                     # 'autovideosink',
#                                     'x264enc',
#                                     'mp4mux ! filesink location=file2.mp4',
#                                     ])

set_gst_debug_level(Gst.DebugLevel.FIXME)

count = 0
def on_callback(buffer,):
    global count
    print(f'on_callback {count = }')
    count += 1



num_buffers, quality = 50, 85

GCS_DISPLAY_PIPELINE = to_gst_string([
            'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
            'queue ! rtph264depay ! avdec_h264',
            'fpsdisplaysink',
        ])

SINK_PIPELINE = to_gst_string([
            'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
            'queue ! rtph264depay ! avdec_h264',
            'fpsdisplaysink',
            # 'autovideosink name=Auto_Display',
        ])

SRC_PIPELINE = to_gst_string([
            'videotestsrc pattern=ball flip=true is-live=true num-buffers=100 ! video/x-raw,framerate={fps}/1',
            'queue leaky=2 ! video/x-raw,format=I420,width={width},height={height}',
            # 'videoconvert',
            # 'queue',
            # 'x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast',
            'x264enc tune=zerolatency',
            'rtph264pay ! udpsink host=127.0.0.1 port={port}',
        ])

SRC_PIPELINE = fstringify(SRC_PIPELINE, quality=85, num_buffers=100, width=720, height=480, fps=30, port=5000)

with GstContext():  # create GstContext (hides MainLoop)
    with GstPipeline(SINK_PIPELINE, debug=False) as rcv_pipeline:  # this will show the video on fpsdisplaysink
    #     command = fstringify(command, quality=quality, num_buffers=num_buffers, width=640, height=480, fps=10)
        je = GstStreamUDP(SRC_PIPELINE, on_callback=on_callback, debug=False).startup()
        time.sleep(3)
        # je.shutdown()
        # while not je.is_done:
        #     time.sleep(.1)
        je.shutdown()
        # print (f"{je.is_done = }")
