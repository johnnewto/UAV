
from gstreamer import GstPipeline, GstContext, GstVideoSave, GstVideoSink, GstVidSrcValve, GstApp, Gst, GstVideo, GstJpegEnc
from gstreamer.utils import *
import time, threading

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
def on_capture():
    print('on_capture')
# if True:
with GstContext(debug=False):  # GST main loop in thread
    with GstPipeline(command1, debug=False) as pipeline1:

        for i in range(1):
            vs = GstVideoSave(f'file{i:03d}.mp4', 1280, 720, status_interval=1, on_status_video_capture=on_capture, debug=False).startup()
            time.sleep(2)
            vs.end_stream()
            # time.sleep(1)
            if vs :
                vs.shutdown()

# je = GstJpegEnc(1280, 720, interval=1, max_count=10, on_jpeg_capture=on_capture, debug=False)
# time.sleep(1)
# je.startup()
# time.sleep(3)
# je.shutdown()



