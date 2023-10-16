
import asyncio
import PySimpleGUI as sg

from UAV.logging import LogLevels

from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil, mavlink
from UAV.utils.general import boot_time_str, read_camera_dict_from_toml

from UAV.camera.gst_cam import GSTCamera
from gstreamer import  GstPipeline, Gst, GstContext, GstPipes
from gstreamer.utils import to_gst_string
import time
from pathlib import Path
# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
from UAV.manager import Gui



DISPLAY_H264_PIPELINE = to_gst_string([
    'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
    'queue ! rtph264depay ! avdec_h264',
    'fpsdisplaysink ',
])
# gst-launch-1.0 udpsrc port=5000 ! application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)RAW,sampling=(string)RGB ! rtpvrawdepay ! videoconvert ! autovideosink
DISPLAY_RAW_PIPELINE = to_gst_string([
    'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB,depth=(string)8, width=(string)640, height=(string)480, payload=(int)96',
    # 'caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB, depth=(string)8, width=(string)640, height=(string)480, payload=(int)96"'
    'rtpvrawdepay videoconvert ! queue',
    'xvimagesink sync=false ',
])
DISPLAY_RAW_PIPELINE = to_gst_string([
    # 'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB,depth=(string)8, width=(string)640, height=(string)480, payload=(int)96',
    'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB,depth=(string)8, width=(string)640, height=(string)480',
    # 'udpsrc port={} caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB, depth=(string)8, width=(string)640, height=(string)480"',
    # 'queue ! rtpvrawdepay ! videoconvert',
    'queue ! rtpvrawdepay ! queue ! videoconvert ! queue',
    'fpsdisplaysink sync=false ',
])
# display_pipelines = [GstPipeline(DISPLAY_H264_PIPELINE.format(5100+i)) for i in range(num_cams)]
num_cams = 2
display_pipelines = [GstPipeline(DISPLAY_RAW_PIPELINE.format(5100 + i)) for i in range(num_cams)]

def display(num_cams=2, udp_encoder='h264'):
    """ Display video from drone"""
    if udp_encoder == 'h264':
        display_pipelines = [GstPipeline(DISPLAY_H264_PIPELINE.format(5100+i)) for i in range(num_cams)]
    else:
        display_pipelines = [GstPipeline(DISPLAY_RAW_PIPELINE.format(5100 + i)) for i in range(num_cams)]

    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread
        with GstPipes(display_pipelines, loglevel=LogLevels.INFO):  # this will show the video on fpsdisplaysink
            while any(p.is_active for p in display_pipelines):
                time.sleep(.5)


async def main(encoder):
    con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
    # logger.disabled = True
    print (f"{boot_time_str =}")
    config_path = Path("../config")
    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread

        with GstPipes(display_pipelines): # this will show the video on fpsdisplaysink
        # with GstPipeline(GCS_DISPLAY_PIPELINE, loglevel=LogLevels.CRITICAL) as rcv_pipeline: # this will show the video on fpsdisplaysink
            # rcv_pipeline.log.disabled = True
            with MAVCom(con1, source_system=111, loglevel=LogLevels.CRITICAL) as GCS_client: # This normally runs on GCS
                with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server: # This normally runs on drone

                    # add GCS manager
                    gcs:CameraClient = GCS_client.add_component( CameraClient(mav_type=mavutil.mavlink.MAV_TYPE_GCS, source_component=11, loglevel=LogLevels.INFO))

                    # add UAV cameras, This normally runs on drone
                    cam_1 = GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"), udp_encoder=encoder, loglevel=LogLevels.DEBUG)
                    cam_2 = GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"), udp_encoder=encoder, loglevel=LogLevels.DEBUG)
                    UAV_server.add_component( CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component= mavutil.mavlink.MAV_COMP_ID_CAMERA, camera=cam_1, loglevel=LogLevels.DEBUG))
                    UAV_server.add_component(CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component= mavutil.mavlink.MAV_COMP_ID_CAMERA2, camera=cam_2, loglevel=LogLevels.DEBUG))

                    # Run the main function using asyncio.run
                    gui = Gui(client=gcs)

                    t1 = asyncio.create_task(gui.find_cameras())
                    t2 = asyncio.create_task(gui.run_gui())

                    try:
                        await asyncio.gather(t1, t2)
                    except asyncio.CancelledError:
                        print("CancelledError")
                        pass



if __name__ == '__main__':
    UDP_ENCODER = 'rawvideo'  # 'h264'
    # ENCODER = 'h264'
    graph = sg.Graph(canvas_size=(700, 300),
                     graph_bottom_left=(0, 0),
                     graph_top_right=(700, 300),
                     background_color='red',
                     enable_events=True,
                     drag_submits=True, key='graph')

    from multiprocessing import Process

    p = Process(target=display, args=(2,UDP_ENCODER))
    p.start()

    asyncio.run(main(UDP_ENCODER))
    p.terminate()