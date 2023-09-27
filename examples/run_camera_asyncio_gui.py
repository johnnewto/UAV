
import asyncio
import PySimpleGUI as sg
from dataclasses import dataclass

from asyncio_gui import Btn_State, FButton, ButtonManager, ControlPanel, create_window
from UAV.logging import LogLevels

from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil, mavlink
from UAV.utils.general import boot_time_str, read_camera_dict_from_toml

from UAV.camera import GSTCamera
from gstreamer import  GstPipeline, Gst, GstContext
import gstreamer.utils as gst_utils
import time
from pathlib import Path
# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)

GCS_DISPLAY_PIPELINE = gst_utils.to_gst_string([
            'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
            'queue ! rtph264depay ! avdec_h264',
            'fpsdisplaysink',
        ])
con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"


async def snapshot_task(client:CameraClient, # mav component
                        comp: int = 22,  # server component ID (camera ID)
                        start:bool=True, # start or stop
                        timeout=5.0): # timeout
    """This is a coroutine function that will be called by the button when pressed."""
    print (f'executing the task {snapshot_task.__name__} {comp=} ')
    ret = await client.image_start_capture(222, comp, 1, 10) if start else await client.image_stop_capture(222, comp)

    if ret and start:
        yield Btn_State.RUNNING
    elif ret and not start:
        yield Btn_State.READY
        return
    else:
        yield Btn_State.FAILED
        return

    while True:
        ret = await client.wait_for_message(mavlink.MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED, 222, comp, 2)
        print(f"Image Request {comp = } {ret = }")
        if not ret:
            print(f"BREAK Image Request {comp = } {ret = }")
            break

    yield Btn_State.READY


async def stream_task(client:CameraClient, # mav component
                        comp: int = 22,  # server component ID (camera ID)
                        start:bool=True, # start or stop
                        timeout=5.0): # timeout
    """This is a coroutine function that will be called by the button when pressed."""
    ret = await client.video_start_streaming(222, comp) if start else await client.video_stop_streaming(222, comp)
    if ret and start:
        yield Btn_State.RUNNING
    elif ret and not start:
        yield Btn_State.READY
        # return
    else:
        yield Btn_State.FAILED
        # return
    # while True:
    #     ret = await client.Await_for_message(mavlink.MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED, 222, comp, timeout=2)
    #     print(f"Image Request {comp = } {ret = }")
    #     if not ret:
    #         print(f"BREAK Image Request {comp = } {ret = }")
    #         break
    #     # await asyncio.sleep(1)
    # # await asyncio.sleep(5)
    # yield Btn_State.READY, "f{snapshot_func.__name__} Ready"

async def record_task(client:CameraClient, # mav component
                        comp: int = 22,  # server component ID (camera ID)
                        start:bool=True, # start or stop
                        timeout=5.0): # timeout
    """This is a coroutine function that will be called by the button when pressed."""
    print(f'executing the task {record_task.__name__} asyncio.sleep({timeout=}) ')
    # print (f'{button.state = }, button_color = {button.button_color}, {button.key = }')
    await asyncio.sleep(timeout)
    return Btn_State.DONE, "f{record_func.__name__} Done"


def add_camera(client, window, manager, comp, buttons=None):
    # Instantiate ControlPanel and extend the window's layout with it
    panel = ControlPanel(comp, buttons=buttons)
    layout = panel.get_layout()
    window.extend_layout(window, [layout])
    for b in panel.buttons:
        manager.register(b)
@dataclass
class Gui():
    client:CameraClient = None
    fc = None
    cameras = []

    new_cam_queue = asyncio.Queue()
    exit_event = asyncio.Event()

    async def find_cameras(self):
        while not self.exit_event.is_set():
            ret = await self.client.wait_heartbeat(remote_mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, timeout=2)
            if ret:
                if ret not in self.cameras:
                    self.cameras.append(ret)
                    await self.new_cam_queue.put(ret)
                    print(f"Put Queue New camera {ret = }")
        print("find_cameras exit")

    async def run_gui(self):
        btn_manager = ButtonManager()
        # layout = [[sg.Button('Info'), sg.B('Cancel'), sg.Button('Exit')]]
        window = create_window([[sg.Button('Info'), sg.B('Cancel'), sg.Button('Exit')]]).finalize()
        # cam_num = add_camera(self.client, window, btn_manager, 0)
        cam_num = 0
        btn_tasks = []
        while True:
            try:
                comp = 22
                # check for new camera, add to window
                system, comp = self.new_cam_queue.get_nowait()
                print(f"Get Queue New camera {system}/{comp}")
                buttons = [FButton(self.client, comp, snapshot_task, 'Snapshot'),
                           FButton(self.client, comp, stream_task, 'Stream'),
                           FButton(self.client, comp, record_task, 'Record')]

                add_camera(self.client, window, btn_manager, comp, buttons=buttons)
                # cam_num = add_camera(self.client, window, btn_manager, cam_num)
            except asyncio.QueueEmpty:
                pass

            event, values = window.read(timeout=1)
            if event == '__TIMEOUT__':
                await asyncio.sleep(0.1)
            else:
                print(event, values)
                btn = btn_manager.find_button(event)
                task = btn.run_task() if btn else None
                if task: btn_tasks.append(task)

            if event == None or event == "Exit":
                for task in btn_tasks:
                    task.cancel()
                self.exit_event.set()
                break

            # elif event == 'Cancel':
            #     self.client.image_stop_capture(222, 22)
            #     for button in manager.buttons:
            #         button.cancel_task()
            #
            #     window[event].update('New Snap Text')

            # elif event == 'Add Control Panel':
            #     buttons = [FButton(None, comp, snapshot_task, 'Snapshot'),
            #                FButton(None, comp, stream_task, 'Stream'),
            #                FButton(None, comp, record_task, 'Record')]
            #
            #     add_camera(self.client, window, btn_manager, comp, buttons=buttons)
            #     # cam_num = add_camera(self.client, window, btn_manager, cam_num)
            await asyncio.sleep(0.1)

        window.close()
        print("run_gui exit")


async def main():

    # logger.disabled = True
    print (f"{boot_time_str =}")
    config_path = Path("../config")
    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread
        with GstPipeline(GCS_DISPLAY_PIPELINE, loglevel=LogLevels.CRITICAL) as rcv_pipeline: # this will show the video on fpsdisplaysink
            # rcv_pipeline.log.disabled = True
            with MAVCom(con1, source_system=111, loglevel=LogLevels.CRITICAL) as GCS_client: # This normally runs on GCS
                with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server: # This normally runs on drone

                    # add GCS manager
                    gcs:CameraClient = GCS_client.add_component( CameraClient(mav_type=mavutil.mavlink.MAV_TYPE_GCS, source_component=11, loglevel=LogLevels.CRITICAL))
                    # gcs.log.disabled = True
                    # add UAV cameras, This normally runs on drone
                    cam_1 = GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"), loglevel=LogLevels.CRITICAL)
                    cam_2 = GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"), loglevel=LogLevels.CRITICAL)
                    UAV_server.add_component(CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component=22, camera=cam_1, loglevel=LogLevels.DEBUG))
                    UAV_server.add_component(CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component=23, camera=cam_2, loglevel=LogLevels.DEBUG))
                    # Run the main function using asyncio.run
                    gui = Gui(client=gcs)

                    t1 = asyncio.create_task(gui.find_cameras())
                    t2 = asyncio.create_task(gui.run_gui())
                    # g.fc = asyncio.create_task(find_cameras(gcs))

                    print("before gather")
                    try:
                        await asyncio.gather(t1, t2)
                    except asyncio.CancelledError:
                        print("CancelledError")
                        pass



if __name__ == '__main__':
    asyncio.run(main())