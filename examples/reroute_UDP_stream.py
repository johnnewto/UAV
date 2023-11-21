import time

import gstreamer.utils as utils
from UAV.utils import helpers
from gstreamer import GstPipeline, Gst

# os.environ["GST_PYTHON_LOG_LEVEL"] = "logging.DEBUG"


DISP_PIPELINE = utils.to_gst_string([
    'udpsrc port=5100 ! application/x-rtp,encoding-name=H265 ! rtph265depay ! decodebin',
    'fpsdisplaysink sync=false'
])
# print(SRC_PIPELINE)
SINK_PIPELINE = utils.to_gst_string([
    'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H265, payload=(int)96',
    'queue leaky=2 ! valve name=myvalve drop=False ! rtph265depay ',
    'rtph265pay config-interval=1 ! udpsink host=127.0.0.1 port=5100 sync=false'
])
print(SINK_PIPELINE)

# num_buffers = 40
# with GstPipeline(SINK_PIPELINE) as rcv_pipeline:
#     rcv_buffers = []
#     for i in range(num_buffers):
#         while not pipeline.is_done:
#             time.sleep(.1)

num_buffers = 200

p = helpers.start_displays(display_type='cv2', decoder='h265', num_cams=2, port=5100)
# utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
if True:
# with GstPipeline(DISP_PIPELINE) as disp_pipeline:  # this will show the video on fpsdisplaysink
    with GstPipeline(SINK_PIPELINE) as pipeline:  # this will show the video on fpsdisplaysink
        buffers = []
        count = 0
        dropstate = False
        while True:
            time.sleep(0.1)
            count += 1
            if count % 50 == 0:

                dropstate = not dropstate
                pipeline.set_valve_state("myvalve", dropstate)
                print(f'{count = } {dropstate = }')
                # pipeline.pipeline.
                # encoder = pipeline.get_by_name("myenc")
                # encoder.set_property("bitrate", 4000)
                # if dropstate:
                #     pipeline._pipeline.set_state(Gst.State.PLAYING)
                # else:
                #     pipeline._pipeline.set_state(Gst.State.PAUSED)
p.terminate()