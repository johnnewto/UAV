
import time
import logging


# from gstreamer import GstContext, GstPipeline, GstVideoSourceValve
# import gstreamer.utils as utils
# import gstreamer
# log = logging.getLogger('pygst')
# log.info('Starting')
from gstreamer import GstContext, GstPipeline, GstVidSrcValve
import gstreamer.utils as utils


# Converts list of plugins to gst-launch string
# ['plugin_1', 'plugin_2', 'plugin_3'] => plugin_1 ! plugin_2 ! plugin_3
DEFAULT_PIPELINE = utils.to_gst_string([
    "videotestsrc num-buffers=20",
    "capsfilter caps=video/x-raw,format=GRAY16_LE,width=640,height=480",
    "queue",
    "appsink emit-signals=True"
])
# print(DEFAULT_PIPELINE)

DEFAULT_PIPELINE = utils.to_gst_string([
            'videotestsrc pattern=smpte is-live=true num-buffers=1000 ! tee name=t',
            't.',
            'queue leaky=2 ! valve name=myvalve drop=False ! video/x-raw,format=I420,width=640,height=480',
            'videoconvert',
            # 'x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast',
            'x264enc tune=zerolatency',
            'rtph264pay ! udpsink host=127.0.0.1 port=5000',
            't.',
            'queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=5/1,format=(string)BGR',
            'videoconvert ! appsink name=mysink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
        ])

# print(DEFAULT_PIPELINE)




command = DEFAULT_PIPELINE
width, height, num_buffers = 1920, 1080, 100
# caps_filter = 'capsfilter caps=video/x-raw,format=RGB,width={},height={}'.format(width, height)
# command = 'videotestsrc num-buffers={} ! {} ! appsink emit-signals=True sync=true'.format(
#     num_buffers, caps_filter)
with GstVidSrcValve(command, leaky=True) as pipeline:
    buffers = []
    count = 0
    dropstate = False
    while len(buffers) < num_buffers:
        time.sleep(0.1)
        count += 1
        if count % 10 == 0:
            # print(f'Count = : {count}')
            dropstate = not dropstate
            pipeline.set_valve_state("myvalve", dropstate)
        buffer = pipeline.pop()
        if buffer:

            buffers.append(buffer)
            # if len(buffers) % 10 == 0:
            #     print(f'Got: {len(buffers)} buffers of {pipeline.queue_size}')
    print('Got: {} buffers'.format(len(buffers)))