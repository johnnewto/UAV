__all__ = ['start_displays']

import time
from multiprocessing import Process
from datetime import datetime
import cv2

try:
    from gstreamer import GstPipeline, GstVideoSource, GstContext, GstPipes
    import gstreamer.utils as gst_utils
    from gstreamer.gst_tools import GstBuffer
except:
    print("GStreamer is not installed")


def start_displays(config_dict, display_type: str = 'cv2',  # display type
                    width=800, height=600,
                   ) -> Process:  # encoder type
    """ Display video from one or more gst streams from drone in a separate process"""
    # if config_dict is None:
    #
    if config_dict['camera_udp_decoder'] == 'h264':
        cmd = 'udpsrc port={port} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96'
        avdec = 'avdec_h264'
        depay = 'rtph264depay'

    elif config_dict['camera_udp_decoder'] == 'h265':
        cmd = 'udpsrc port={port} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H265, payload=(int)96'
        avdec = 'avdec_h265'
        depay = 'rtph265depay'

    elif config_dict['camera_udp_decoder'] == 'rtsp':
        cmd = 'rtspsrc location=rtsp://admin:admin@192.168.144.108:554/cam/realmonitor?channel=1&subtype=0 latency=100 '
        avdec = 'avdec_h265'
        depay = 'rtph265depay'
        #gst-launch-1.0 rtspsrc location="rtsp://admin:admin@192.168.144.108:554/cam/realmonitor?channel=1&subtype=0" latency=1000queue ! rtph265depay ! h265parse ! avdec_h265 ! autovideosink

    else:
        raise ValueError(f"Unknown decoder type {config_dict['udp_decoder'] }")

    if display_type == 'gst':
        _dict = {
            'port': '{}', 'avdec': avdec, 'depay': depay,
            'pipeline': [
                cmd,
                'queue',
                '{depay} ! {avdec}',
                'videoconvert',
                'fpsdisplaysink',
            ],
        }
    else:
        _dict = {
            'port': '{}', 'avdec': avdec, 'depay': depay,
            'pipeline': [
                cmd,
                'queue',
                '{depay} ! {avdec}',
                'videoconvert',
                'capsfilter caps=video/x-raw,format=BGR ',
                'appsink name=mysink emit-signals=true  sync=false ',
                #
                # 'appsink name=mysink emit-signals=True max-buffers=1 drop=True sync=false',
            ],
        }

    # def gst_display(_num_cams: int, _port: int):
    def gst_display(_names: list, ports: list):
        """ Display video from one or more gst streams"""
        command_display = gst_utils.format_pipeline(**_dict)
        print('gst_display', command_display)
        pipes = [GstPipeline(command_display.format(_port)) for _port in ports]

        # if True:
        # with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread
        # with GstPipes(pipes, loglevel=LogLevels.INFO) as gp:
        gp = GstPipes(pipes, loglevel=20).startup()
        while any(pipe.is_active for pipe in pipes):
            time.sleep(.5)
        gp.shutdown()

    def cv2_display(_names: list, _ports: list, width=width, height=height):
        """ Display video from one or more gst streams"""
        command_display = gst_utils.format_pipeline(**_dict)
        print('cv2_display', command_display)

        _num_cams = len(_names)

        pipes = [GstVideoSource(command_display.format(port)) for port in _ports]

        for name in _names:
            cv2.namedWindow(name, cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow(name, width, height)

        with GstPipes(pipes, loglevel=10):
            # time.sleep(1)
            buffer = [GstBuffer for _ in range(_num_cams)]
            count = 0
            while any(pipe.is_active for pipe in pipes):
                count += 1
                for i, pipe in enumerate(pipes):
                    # buffer = pipe.pop()
                    buffer[i] = pipe.get_nowait()
                    if buffer[i]:
                        if count % 100 == 0:
                            print(f'buffer[{i}].data.shape = {buffer[i].data.shape}')
                        # put in presentation time stamp
                        secs = buffer[i].pts / 1000000000
                        pts = datetime.fromtimestamp(secs)
                        position = (10, 170)  # (x, y) coordinates
                        # number = str(pts)
                        _pts = pts.strftime('%M:%S.%f')
                        # Use OpenCV to put the pts on the image
                        im = buffer[i].data.copy()  # recent cv2 needs this to be a copy if you want to draw on it
                        cv2.putText(im, _pts, position, cv2.FONT_HERSHEY_SIMPLEX, 2, (255), 2)

                        cv2.imshow(_names[i],im)

                cv2.waitKey(10)
                if not any(buffer):
                    time.sleep(0.01)

        cv2.destroyAllWindows()

    target = gst_display if display_type == 'gst' else cv2_display
    ports = config_dict['camera_ip_ports']
    names = config_dict['camera_names']
    _p = Process(target=target, args=(names, ports))
    _p.start()
    time.sleep(0.1)  # wait for display to start
    return _p



if __name__ == '__main__':
    from UAV.utils.general import  toml_load, config_dir
    width, height, fps, num_buffers = 1920, 1080, 30, 200
    caps_filter = 'capsfilter caps=video/x-raw,format=RGB,width={},height={},framerate={}/1'.format(width, height, fps)
    command = 'videotestsrc is-live=true num-buffers={} ! {} ! timeoverlay !  appsink emit-signals=True sync=false'.format(num_buffers, caps_filter)

    # p = start_displays(display_type='cv2', num_cams=5)
    client_config_dict = toml_load(config_dir() / f"client_config.toml")
    p = start_displays(client_config_dict, display_type='cv2')

    with GstContext():
        with GstPipeline(command, loglevel=10):
            time.sleep(5)
    p.terminate()
