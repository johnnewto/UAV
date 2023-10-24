import time

import gstreamer.utils as gst_utils
from UAV.logging import LogLevels
from UAV.utils import start_displays
from gstreamer import GstPipeline, Gst, GstContext
from gstreamer.utils import to_gst_string


cmd1 = "videotestsrc pattern=ball is-live=true ! clockoverlay ! capsfilter caps=video/x-raw,format=BGR,width=640,height=480,framerate=30/1 ! queue ! interpipesink name=video_src"

cmd2 = "interpipesrc listen-to=video_src is-live=true allow-renegotiation=true  accept-events=false ! queue ! videoconvert ! fpsdisplaysink sync=false"

cmd3 = "interpipesrc listen-to=video_src is-live=true allow-renegotiation=true   accept-events=false ! queue ! fpsdisplaysink sync=false"

cmd4 = "interpipesrc listen-to=video_src is-live=true allow-renegotiation=false ! queue ! xvimagesink sync=true"

cmd5 = to_gst_string([
    'interpipesrc listen-to=video_src allow-renegotiation=false format=time',
    'valve name=myvalve drop=False ',
    'queue',
    # 'capsfilter caps=video/x-raw,format=BGR,width=640,height=480,framerate=10/1',
    'videoconvert',
    'x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast',
    # 'x264enc tune=zerolatency',
    'rtph264pay ! udpsink host=127.0.0.1 port=5000',
    ])

cmd6 = to_gst_string([
    'interpipesrc listen-to=video_src is-live=True  emit-signals=true allow-renegotiation=false do-timestamp = false format=time',
    'valve name=myvalve drop=False ',
    'queue',
    # 'capsfilter caps=video/x-raw,format=BGR,width=640,height=480,framerate=10/1',
    'videoconvert',
    'x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast',
    # 'x264enc tune=zerolatency',
    'rtph264pay ! udpsink host=127.0.0.1 port=5001',
    ])



# gst_utils.set_gst_debug_level(Gst.DebugLevel.INFO)
if __name__ == "__main__":
    p = start_displays(num_cams=2, port=5000)
    time.sleep(0.5)
    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread
        with GstPipeline(cmd1, loglevel=LogLevels.DEBUG) as p_src:
            time.sleep(0.2)
            with (GstPipeline(cmd5, loglevel=10) as p_sink1, GstPipeline(cmd6, loglevel=10) as p_sink2):  # , GstPipeline(cmd3, loglevel=10):
                # p_src.play()
                time.sleep(2)
                for i in range(5):
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Pause")
                    p_sink1.set_valve_state("myvalve", True)
                    p_sink2.set_valve_state("myvalve", True)
                    time.sleep(4)

                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Play")
                    p_sink1.set_valve_state("myvalve", False)
                    p_sink2.set_valve_state("myvalve", False)
                    time.sleep(4)
                # p_src.pause()
                # with (GstPipeline(cmd5, loglevel=10) as p_sink1, GstPipeline(cmd6, loglevel=10) as p_sink2): #, GstPipeline(cmd3, loglevel=10):

            # time.sleep(1)
            # p_src.pause()
        # with GstPipeline(cmd1, loglevel=LogLevels.DEBUG) as p_src:
        #     gst_utils.set_gst_debug_level(Gst.DebugLevel.DEBUG)
        #     with GstPipeline(cmd6, loglevel=10): #, GstPipeline(cmd3, loglevel=10):
        #         # p_src.play()
        #         time.sleep(12)

            # with GstPipeline(cmd3, loglevel=10):
            #     time.sleep(3)

    p.terminate()