__all__ = ['start_displays', 'dotest']

import time
from UAV.logging import LogLevels
from multiprocessing import Process
from typing import Dict

import gstreamer.utils as gst_utils

from UAV.utils import toml_load, config_dir
from gstreamer import GstPipeline, GstContext, GstPipes


# display_pipelines = [GstPipeline(DISPLAY_RAW_PIPELINE.format(5000 + i)) for i in range(num_cams)]

def start_displays(_dict: Dict = None,  # camera dict
                   num_cams: int = 1,  # number of cameras
                   port: int = 5000,  # port number
                   ) -> Process:  # encoder type
    """ Display video from one or more gst streams from drone in a separate process"""
    if _dict is None:
        _dict = {
            'port': 5000,
            'pipeline': [
                'udpsrc port={port} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
                'queue',
                'rtph264depay ! avdec_h264',
                'videoconvert',
                'fpsdisplaysink',
            ],
        }

    def display(_num_cams: int, _port: int):
        """ Display video from one or more gst streams"""
        print(_dict)
        command_display = gst_utils.format_pipeline(**_dict)
        command_display = command_display.replace('port=5000', 'port={}')
        pipes = [GstPipeline(command_display.format(_port + i)) for i in range(_num_cams)]

        # if True:
        # with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread
        # with GstPipes(pipes, loglevel=LogLevels.INFO) as gp:
        gp = GstPipes(pipes, loglevel=20).startup()
        while any(pipe.is_active for pipe in pipes):
            time.sleep(.5)
        gp.shutdown()


    _p = Process(target=display, args=(num_cams, port))
    _p.start()
    return _p

def dotest():
    def _dotest():
        # with GstContext(loglevel=LogLevels.CRITICAL):
        while True:
            time.sleep(1)
            print("sleep")

    _p = Process(target=_dotest)
    _p.start()
    return _p


if __name__ == '__main__':
    camera_dict = toml_load(config_dir() / "test_camera_0.toml")
    # display_dict = camera_dict['gstreamer_h264_udp_displaysink']
    # p = start_displays(display_dict, num_cams=5)
    p = start_displays(num_cams=5)
    command = gst_utils.format_pipeline(**camera_dict['gstreamer_videotestsrc'])
    with GstContext(), GstPipeline(command, loglevel=10):
        time.sleep(5)
    p.terminate()
