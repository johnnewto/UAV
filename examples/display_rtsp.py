import time

import gstreamer.utils as utils
from UAV.utils import helpers
from gstreamer import GstPipeline, Gst

p = helpers.start_displays(display_type='cv2', decoder='rtsp', num_cams=1)


while True:
    time.sleep(0.1)

p.terminate()