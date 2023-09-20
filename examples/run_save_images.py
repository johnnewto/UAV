
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

count = 0
def on_capture(buffer,):
    global count
    print('on_capture')
    filename = f"snapshot_{count:03d}.jpg"
    print(f'saved {filename = }')
    with open(filename, 'wb') as f:
        f.write(buffer)
        count += 1
# if True:
# with GstContext(debug=False):  # GST main loop in thread
#     with GstPipeline(command1, debug=False) as pipeline1:

        # for i in range(1):
        #     vs = GstVideoSave(f'file{i:03d}.mp4', 1280, 720, status_interval=1, on_status_video_capture=on_capture, debug=False).startup()
        #     time.sleep(2)
        #     vs.end_stream()
        #     # time.sleep(1)
        #     # vs.shutdown()

# je = GstJpegEnc(1280, 720, interval=1, max_count=10, on_jpeg_capture=on_capture, debug=False)
# time.sleep(1)
# je.startup()
# time.sleep(3)
# je.shutdown()


from gstreamer import GstVideoSource

width, height, num_buffers = 1920, 1080, 100
caps_filter = 'capsfilter caps=video/x-raw,format=RGB,width={},height={}'.format(width, height)
command = 'videotestsrc num-buffers={} ! {} ! appsink emit-signals=True sync=false'.format(
num_buffers, caps_filter)

# if isinstance(variable, list):

command = to_gst_string([
    # 'intervideosrc channel=channel_1  ',
     'videotestsrc pattern=ball num-buffers={num_buffers}',
     'videoconvert',
     'videoscale ! video/x-raw,width={width},height={height},framerate={fps}/1',
     'jpegenc quality={quality}',   # Quality of encoding, default is 85
# "capsfilter caps=video/x-raw,format=GRAY16_LE,width=640,height=480",
# "queue",
     # "videoconvert ! videorate drop-only=true ! video/x-raw,framerate=10/1,format=(string)BGR",
    #  "videoconvert ! appsink name=mysink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ",
     'appsink name=mysink emit-signals=True max-buffers=1 drop=True',
    # "videotestsrc num-buffers=100",
    # "capsfilter caps=video/x-raw,format=GRAY16_LE,width=640,height=480",
    # "queue",
    # "appsink emit-signals=True"
])


num_buffers, quality = 50, 85

print(f"{command = }")

command = to_gst_string([
    # 'intervideosrc channel=channel_1  ',
     'videotestsrc pattern=ball num-buffers={num_buffers}',
     'videoconvert',
     'videoscale ! video/x-raw,width={width},height={height},framerate={fps}/1',
     'jpegenc quality={quality}',   # Quality of encoding, default is 85
     'appsink name=mysink emit-signals=True max-buffers=1 drop=True',
])
with GstContext():  # create GstContext (hides MainLoop)
    command = fstringify(command, quality=quality, num_buffers=num_buffers, width=640, height=480, fps=10)
    je = GstJpegEnc(command, max_count=10, on_jpeg_capture=on_capture, debug=False).startup()

    while not je.is_done:
        time.sleep(.1)

    print (f"{je.is_done = }")
