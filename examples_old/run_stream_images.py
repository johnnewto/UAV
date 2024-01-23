import logging

from gstreamer import GstPipeline, GstContext, GstStreamUDP
from gstreamer.utils import *
import time
from UAV.logging import LogLevels

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


set_gst_debug_level(Gst.DebugLevel.FIXME)

count = 0
def on_callback(buffer,):
    global count
    print(f'on_callback {count = }')
    count += 1

num_buffers, quality = 50, 85

SRC_PIPELINE = to_gst_string([
            'videotestsrc pattern=ball flip=true is-live=true num-buffers=110 ! video/x-raw,framerate=10/1 !  tee name=t',
            # 't.',
            # 'queue leaky=2 ! valve name=myvalve drop=True ! video/x-raw,format=I420,width=640,height=480',
            # 'textoverlay text="Frame: " valignment=top halignment=left shaded-background=true',
            # 'timeoverlay valignment=top halignment=right shaded-background=true',
            't.',
            'queue',
            'videoconvert',
            # 'x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast',
            'x264enc tune=zerolatency',
            'rtph264pay ! udpsink host=127.0.0.1 port=5000',

            "t.",
            'queue ! autovideosink',

            "t.",
            'queue ! intervideosink channel=channel_0  ',
    ])

DISP_PIPELINE = to_gst_string([
            'intervideosrc channel=channel_0  ',
            'videoconvert',
            'fpsdisplaysink',
            # 'autovideosink',
        ])

SINK_PIPELINE = to_gst_string([
            'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
            # 'queue',
            'rtph264depay ! avdec_h264',
            'fpsdisplaysink',
            # 'autovideosink name=Auto_Display',
        ])


SRC_PIPELINE = fstringify(SRC_PIPELINE, quality=85, num_buffers=100, width=640, height=480, fps=30, port=5000)

with GstContext():  # create GstContext (hides MainLoop)
    with GstPipeline(SINK_PIPELINE, loglevel=LogLevels.DEBUG) as rcv_pipeline:  # this will show the video on fpsdisplaysink
    #     command = fstringify(command, quality=quality, num_buffers=num_buffers, width=640, height=480, fps=10)
        with GstStreamUDP(SRC_PIPELINE, on_callback=on_callback, loglevel=LogLevels.DEBUG) as je:
            with GstPipeline(DISP_PIPELINE, loglevel=LogLevels.DEBUG) as disp_pipeline:
                # time.sleep(3)
                # # je.shutdown()
                # #
                while not je.is_done:
                    time.sleep(.1)
                print (f"{je.is_done = }")

        # je = GstStreamUDP(SRC_PIPELINE, on_callback=on_callback, loglevel=LogLevels.DEBUG).startup()
        # time.sleep(3)
        # # je.shutdown()
        # # while not je.is_done:
        # #     time.sleep(.1)
        # je.shutdown()
        # # print (f"{je.is_done = }")
