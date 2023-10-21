from UAV.logging import LogLevels

from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil
from UAV.utils.general import boot_time_str, toml_load, config_dir

from UAV.camera import GSTCamera
from gstreamer import  GstPipeline, Gst, GstContext
import gstreamer.utils as gst_utils
import time
from pathlib import Path
# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
import PySimpleGUI as sg

# Class holding the button graphic info. At this time only the state is kept
class BtnInfo:
    def __init__(self, state=True, ):
        self._down = state        # Can have 3 states - True, False, None (disabled)
        self.callback = None

    @property
    def down(self):
        return self._down

def gui():
    sg.theme('LightGreen')

    # define the window layout
    layout = [
        [sg.Text('Camera Gui', size=(60, 1), justification='center')],
        # [sg.Image(filename='', key='-IMAGE-')],
        [sg.Button('Toggle', size=(10, 1), k='-TOGGLE1-', border_width=0, button_color='white on green', metadata=BtnInfo())],

        [sg.Button('Snapshot', size=(10, 1)), sg.Button('Stream', size=(10, 1)), sg.Button('Record', size=(10, 1), button_color='white on green'),],
        [sg.ProgressBar(max_value=100, orientation='h', size=(100, 20), key='-PROGRESS-'),],
        # [sg.Button('Stream', size=(10, 1)), sg.Slider((0, 360), 180, 1, orientation='h', size=(40, 15), key='-YAW-', enable_events = True)],
        # [sg.Button('Pitch', size=(10, 1)), sg.Slider((-100, 60), 0, 1, orientation='h', size=(40, 15), key='-PITCH-', enable_events=True)],
        [sg.Radio('None', 'Radio', True, size=(10, 1))],
        [sg.Radio('threshold', 'Radio', size=(10, 1), key='-THRESH-'),
        sg.Slider((0, 255), 128, 1, orientation='h', size=(40, 15), key='-THRESH SLIDER-')],
        [sg.Radio('canny', 'Radio', size=(10, 1), key='-CANNY-'),
        sg.Slider((0, 255), 128, 1, orientation='h', size=(20, 15), key='-CANNY SLIDER A-'),
        sg.Slider((0, 255), 128, 1, orientation='h', size=(20, 15), key='-CANNY SLIDER B-')],
        [sg.Radio('blur', 'Radio', size=(10, 1), key='-BLUR-'),
        sg.Slider((1, 11), 1, 1, orientation='h', size=(40, 15), key='-BLUR SLIDER-')],
        [sg.Radio('hue', 'Radio', size=(10, 1), key='-HUE-'),
        sg.Slider((0, 225), 0, 1, orientation='h', size=(40, 15), key='-HUE SLIDER-')],
        [sg.Radio('enhance', 'Radio', size=(10, 1), key='-ENHANCE-'),
        sg.Slider((1, 255), 128, 1, orientation='h', size=(40, 15), key='-ENHANCE SLIDER-')],

        [sg.Text()],
        [sg.Text('           '),sg.RealtimeButton(sg.SYMBOL_UP, key='-GIMBAL-UP-')],
        [sg.RealtimeButton(sg.SYMBOL_LEFT, key='-GIMBAL-LEFT-'), sg.Text(size=(10,1), key='-STATUS-', justification='c', pad=(0,0)),
        sg.RealtimeButton(sg.SYMBOL_RIGHT, key='-GIMBAL-RIGHT-')],
        [sg.Text('           '), sg.RealtimeButton(sg.SYMBOL_DOWN, key='-GIMBAL-DOWN-')],[sg.Text()],
        [sg.Button('Hide', size=(10, 1)), sg.Column([[sg.Button('Exit', size=(10, 1))]], justification='r')],
    ]



    # create the window and show it without the plot
    return sg.Window('OpenCV Integration', layout, location=(800, 400))


GCS_DISPLAY_PIPELINE = gst_utils.to_gst_string([
            'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
            'queue ! rtph264depay ! avdec_h264',
            'fpsdisplaysink',
        ])
con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
# con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB0"
# con1 = "udpin:192.168.122.84:14445"
if __name__ == '__main__':
    # logger.disabled = True
    window = gui()
    window.Finalize()
    print (f"{boot_time_str =}")

    with GstContext(loglevel=LogLevels.INFO):  # GST main loop in thread
        with GstPipeline(GCS_DISPLAY_PIPELINE, loglevel=LogLevels.CRITICAL) as rcv_pipeline: # this will show the video on fpsdisplaysink
            # rcv_pipeline.log.disabled = True
            with MAVCom(con1, source_system=111, loglevel=LogLevels.CRITICAL) as GCS_client: # This normally runs on GCS
                with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server: # This normally runs on drone
                    # UAV_server.log.disabled = True
                    # GCS_client.log.disabled = True

                    # add GCS manager
                    gcs:CameraClient = GCS_client.add_component( CameraClient(mav_type=mavutil.mavlink.MAV_TYPE_GCS, source_component=11, loglevel=LogLevels.INFO) )
                    # gcs.log.disabled = True
                    # add UAV cameras, This normally runs on drone
                    cam_1 = GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_0.toml"), loglevel=LogLevels.INFO).open()
                    # cam_1.log.disabled = True
                    cam_2 = GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_0.toml"), loglevel=LogLevels.INFO).open()
                    UAV_server.add_component( CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component=22, camera=cam_1, loglevel=LogLevels.INFO))
                    UAV_server.add_component(CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component=23, camera=None, loglevel=LogLevels.INFO))
                    # gimbal_cam_3 = UAV_server.add_component(GimbalServer(mav_type=mavutil.mavlink.MAV_TYPE_GIMBAL, source_component=24, debug=False))
                    # GCS client requests
                    gcs.wait_heartbeat(target_system=222, target_component=22, timeout=1)
                    # gcs.set_target(222, 22)

                    # gcs.request_camera_information(222, 23)
                    # gcs.request_camera_settings(222, 22)
                    #
                    # # capture 5 images from camera 22 and 23
                    # gcs.image_start_capture(222, 22, interval=0.1, count=5)
                    # gcs.image_start_capture(222, 22, interval=1, count=5)  # todo wait for first capture to finish
                    # gcs.image_start_capture(222, 22, interval=1, count=5)
                    down = True
                    while True:
                        event, values = window.read(timeout=50)
                        if event in (sg.WIN_CLOSED, 'Exit'):
                            break
                        if event in ('Hide'):
                            window.hide()
                        if '-TOGGLE1-' in event:
                            window[event].metadata.state = not window[event].metadata.state
                            window[event].update(
                                                 button_color='white on green' if down else 'white on red')
                        elif event == 'Snapshot':
                            down = not down
                            btn = window[event]
                            btn.update(button_color='white on green' if btn.metadata.down else 'white on red')
                            gcs.image_start_capture(222, 22, interval=0.1, count=5)

                        # if '-TOGGLE1-' in event:
                        #     window[event].metadata.state = not window[event].metadata.state
                        # if event in (['Snapshot', 'Down', 'Snap', 'Record']):
                        if 'Snapshot' in event:
                            gcs.image_start_capture(222, 22, interval=0.1, count=5)
                        if 'Stream' in event:
                            gcs.video_start_streaming(222, 22)
                        if 'Record' in event:
                            gcs.video_start_capture(222, 22, frequency=1)



                    print("Exiting")
                    # time.sleep(5)
                    # UAV_server.component[22].camera.list_files()
                    # # # # gcs.image_start_capture(222, 23, interval=1, count=5)
                    # # #
                    # # #
                    # # # # Start & stop drone video capture
                    # gcs.video_start_capture(222, 22, frequency=1)
                    # time.sleep(2)
                    # gcs.video_stop_capture(222, 22)   # todo create new file on drone
                    # time.sleep(1)
                    # # # #
                    # # UAV_server.component[22].camera.list_files()
                    # # # Start & stop drone video streaming camera 22
                    # for i in range (2):
                    #     gcs.video_start_streaming(222, 22)
                    #     time.sleep(1)
                    #     # gcs.request_storage_information(222, 22)
                    #     gcs.video_stop_streaming(222, 22)
                    #     # gcs.request_camera_information(222, 22)
                    #     time.sleep(1)
                    #     gcs.request_camera_capture_status(222, 22)
                    #
                    # time.sleep(2)
                    # UAV_server.component[22].camera.list_files()
                    # gcs.video_start_streaming(222, 22)
                    # gcs.video_start_streaming(222, 22)
                    # time.sleep(2)
                    # # gcs.request_storage_information(222, 22)
                    # gcs.video_stop_streaming(222, 22)

if __name__ == '__main__':
    pass

