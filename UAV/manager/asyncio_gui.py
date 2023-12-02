from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import List, Callable

import PySimpleGUI as sg
import cv2

import gstreamer.utils as gst_utils
from UAV.camera_sdks.viewsheen.gimbal_cntrl import KeyReleaseThread
from UAV.mavlink import CameraClient
from UAV.mavlink import mavlink
from UAV.mavlink import mavutil
from UAV.mavlink.gimbal_client import GimbalClient
from gstreamer import GstVideoSource


class Btn_State:
    """ States of the button that executes a function and awaits the result """
    RUNNING = 1
    READY = 0
    DONE = 2
    FAILED = 3
    CANCELLED = 4


print(f'{Btn_State.RUNNING = }')


async def proto_task(client: any,  # mav component
                     comp: int = 22,  # server component ID (cameras ID)
                     start: bool = True,  # start or stop
                     timeout=5.0):  # timeout
    yield Btn_State.RUNNING
    await asyncio.sleep(timeout)


class FButton:
    """ A class to manage a button that executes a function and awaits the result """

    def __init__(self, client, comp: int, function: proto_task, button_text: str):
        self.client = client
        self.comp = comp
        self.function: proto_task = function
        self.button_text = button_text
        self.key = f'{self.button_text}_{comp}'

        self.button_color = 'white on green'
        self.state = Btn_State.READY
        self.button = sg.Button(button_text=self.button_text, key=f'{self.button_text}_{comp}', button_color=self.button_color)

    def __repr__(self):
        return f'FunctionButton({self.button.key})'

    def __str__(self):
        return f'FunctionButton({self.button.key})'

    def set_state(self, state: int):
        self.state = state
        if state == Btn_State.READY:
            self.button_color = 'white on green'
        if state == Btn_State.RUNNING:
            self.button_color = 'white on red'
        elif state == Btn_State.DONE:
            self.button_color = 'white on blue'
        elif state == Btn_State.FAILED:
            self.button_color = 'black on orange'
        elif state == Btn_State.CANCELLED:
            self.button_color = 'black on yellow'
        # self.down else 'white on red'
        self.button.update(button_color=self.button_color)
        # print(f'FunctionButton {self.key} state set to {self.down}')

    async def task(self, start, timeout=3):
        # proto_task()
        async for state in self.function(self.client, self.comp, start, timeout=timeout):
            self.set_state(state)

    def run_task(self):
        # return asyncio.create_task(self.function(start=True))
        if self.state == Btn_State.READY:
            return asyncio.create_task(self.task(True))
        elif self.state == Btn_State.RUNNING:
            return asyncio.create_task(self.task(False))
        elif self.state == Btn_State.FAILED:
            return asyncio.create_task(self.task(True))

    def get_element(self):
        return self.button

    def cancel_task(self):
        pass


class ButtonManager:
    def __init__(self):

        self.buttons: List[FButton] = []

    def register(self, func_button):
        self.buttons.append(func_button)

    def find_button(self, event):
        for button in self.buttons:
            if event == button.key:
                return button
        return None


class ControlPanel:
    def __init__(self, comp, buttons=None):
        self.name = f'CP-{comp}'
        self.comp = comp
        self.buttons = buttons

    def get_layout(self):
        return [sg.T(f"{self.comp:3d}"), *[b.get_element() for b in self.buttons], sg.I()]


def add_camera(client, window, manager, comp, buttons=None):
    # Instantiate ControlPanel and extend the window's layout with it
    panel = ControlPanel(comp, buttons=buttons)
    layout = panel.get_layout()
    window.extend_layout(window, [layout])
    for b in panel.buttons:
        manager.register(b)


def create_window(layout=None):
    """ Create a base layout and window"""
    if layout is None:
        layout = [
            # [
            [sg.Button('Add Control Panel'), sg.B('Cancel'), sg.Button('Exit')],
            # panel.get_layout(),
        ]
    window = sg.Window('Basic Camera Manager', layout)
    return window


async def snapshot_task(client: CameraClient,  # mav component
                        comp: int,  # server component ID (cameras ID)
                        start: bool = True,  # start or stop
                        timeout=5.0):  # timeout
    """This is a coroutine function that will be called by the button when pressed."""
    print(f'executing the task {snapshot_task.__name__} {comp=} ')
    ret = await client.image_start_capture(222, comp, 1, 5) if start else await client.image_stop_capture(222, comp)

    if ret and start:
        yield Btn_State.RUNNING
    elif ret and not start:
        yield Btn_State.READY
        return
    else:
        yield Btn_State.FAILED
    #     return
    #
    # while True:
    #     # cb = client.register_message_callback(mavlink.MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED, 222, comp, 2)
    #     # client.set_message_callback_cond(mavlink.MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED, 222, comp )
    #     ret = await client.message_callback_cond(mavlink.MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED, 222, comp, 2)
    #     print(f"Image Request {comp = } {ret = }")
    #     if not ret:
    #         print(f"BREAK Image Request {comp = } {ret = }")
    #         break
    #
    # yield Btn_State.READY


async def stream_task(client: CameraClient,  # mav component
                      comp: int,  # server component ID (cameras ID)
                      start: bool = True,  # start or stop
                      timeout=5.0):  # timeout
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


async def record_task(client: CameraClient,  # mav component
                      comp: int,  # server component ID (cameras ID)
                      start: bool = True,  # start or stop
                      timeout=5.0):  # timeout
    """This is a coroutine function that will be called by the button when pressed."""
    print(f'executing the task {record_task.__name__} asyncio.sleep({timeout=}) ')
    # print (f'{button.state = }, button_color = {button.button_color}, {button.key = }')
    await asyncio.sleep(timeout)
    return Btn_State.DONE, "f{record_func.__name__} Done"


@dataclass
class Gui:
    camera_client: CameraClient | None = None
    gimbal_client: GimbalClient | None = None
    auto: Callable = None
    reset: Callable = None
    pause: Callable = None
    fc = None
    cameras = []
    gimbals = []

    new_cam_queue = asyncio.Queue()
    exit_event = asyncio.Event()

    async def find_cameras(self):
        while not self.exit_event.is_set():
            ret = await self.camera_client.wait_heartbeat(remote_mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, timeout=2)
            if ret:
                if ret not in self.cameras:
                    self.cameras.append(ret)
                    await self.new_cam_queue.put(ret)
                    print(f" Found Camera {ret[0]}/{ret[1]}")
        print("find_cameras exit")

    async def find_gimbals(self):
        """ Find all gimbals, add to gimbals list    """
        while not self.exit_event.is_set():
            ret = await self.gimbal_client.wait_heartbeat(remote_mav_type=mavlink.MAV_TYPE_GIMBAL, timeout=0.5)
            if ret:
                if ret not in self.gimbals:
                    self.gimbals.append(ret)
                    await asyncio.sleep(0.1)
                    # await self.new_cam_queue.put(ret)
                    print(f" Found Gimbal {ret[0]}/{ret[1]}")
        print("find_gimbals exit")

    async def find_gimbal(self):
        """ Find a gimbal, return on first found    """
        while not self.exit_event.is_set():
            ret = await self.gimbal_client.wait_heartbeat(remote_mav_type=mavlink.MAV_TYPE_GIMBAL, timeout=0.5)
            if ret:
                print(f" Found Gimbal {ret[0]}/{ret[1]}")
                return ret
        print("find_gimbal exit")

    async def run_gui(self):
        if self.camera_client is None:
            logging.error("Gui has no client")
        if not callable(self.auto):
            logging.warning("Gui auto is not callable")
        if not callable(self.reset):
            logging.warning("Gui reset is not callable")
        if not callable(self.pause):
            logging.warning("Gui pause is not callable")

        btn_manager = ButtonManager()
        window = create_window([[sg.Button('Info'), sg.B('Auto'), sg.B('Reset'), sg.B('Pause'), sg.Button('Exit')]]).finalize()
        window.bind('<Right>', '__GIMBAL_RIGHT__')
        window.bind('<Left>', '__GIMBAL_LEFT__')
        window.bind('<Up>', '__GIMBAL_UP__')
        window.bind('<Down>', '__GIMBAL_DOWN__')

        btn_tasks = []
        while True:
            try:
                # check for new cameras, add to window
                system, comp = self.new_cam_queue.get_nowait()
                # print(f"Get Queue New cameras {system}/{comp}")
                buttons = [FButton(self.camera_client, comp, snapshot_task, 'Snapshot'),
                           FButton(self.camera_client, comp, stream_task, 'Stream'),
                           FButton(self.camera_client, comp, record_task, 'Record')]

                add_camera(self.camera_client, window, btn_manager, comp, buttons=buttons)
            except asyncio.QueueEmpty:
                pass

            event, values = window.read(timeout=1)
            if event == '__TIMEOUT__':
                await asyncio.sleep(0.01)


            elif event == '__GIMBAL_RIGHT__':
                print("Gimbal Right")

                # await self.gimbal_client.cmd_pitch_yaw(0, 10, 0, 0, 0, 0, 222, mavlink.MAV_COMP_ID_GIMBAL)
                self.gimbal_client.manual_pitch_yaw(0, 1, 0, 0, 0, 0, 222, mavlink.MAV_COMP_ID_GIMBAL)

            elif event == '__GIMBAL_LEFT__':
                print("Gimbal Left")
                # await self.gimbal_client.cmd_pitch_yaw(0, -10, 0, 0, 0, 0, 222, mavlink.MAV_COMP_ID_GIMBAL)
                self.gimbal_client.manual_pitch_yaw(0, -1, 0, 0, 0, 0, 222, mavlink.MAV_COMP_ID_GIMBAL)
            elif event == '__GIMBAL_UP__':
                print("Gimbal Up")
                # await self.gimbal_client.cmd_pitch_yaw(10, 0, 0, 0, 0, 0, 222, mavlink.MAV_COMP_ID_GIMBAL)
                self.gimbal_client.manual_pitch_yaw(1, 0, 0, 0, 0, 0, 222, mavlink.MAV_COMP_ID_GIMBAL)
            elif event == '__GIMBAL_DOWN__':
                print("Gimbal Down")
                # await self.gimbal_client.cmd_pitch_yaw(-10, 0, 0, 0, 0, 0, 222, mavlink.MAV_COMP_ID_GIMBAL)
                self.gimbal_client.manual_pitch_yaw(-1, 0, 0, 0, 0, 0, 222, mavlink.MAV_COMP_ID_GIMBAL)


            elif event == None or event == "Exit":
                for task in btn_tasks:
                    task.cancel()
                self.exit_event.set()
                break
            elif event == "Info":
                print(""" This script is designed to fly on the streets of the Neighborhood environment
                            and assumes the unreal position of the drone is [160, -1500, 120].  """)

            elif event == 'Auto':
                try:
                    self.auto()
                    print("Auto done")
                except Exception as e:
                    print(f" Error in Auto: {e}")

            elif event == 'Reset':
                try:
                    self.reset()
                    print("Reset done")
                except Exception as e:
                    print(f" Error in Reset: {e}")

            elif event == 'Pause':
                try:
                    self.pause()
                    print("Pause done")
                except Exception as e:
                    print(f" Error in Pause: {e}")

            else:
                btn = btn_manager.find_button(event)
                task = btn.run_task() if btn else None
                if task: btn_tasks.append(task)
                # await task
                print(f" {(event, values) = } {len(btn_tasks) = } ")
        window.close()
        print("run_gui exit")

    async def gimbal_view(self, width=800, height=600):
        if self.gimbal_client is None:
            logging.error("Gui has no client")

        GIMBAL_PIPELINE = gst_utils.to_gst_string([
            # 'rtspsrc location=rtsp://admin:admin@192.168.144.108:554 latency=100 ! queue',
            'udpsrc port=5010 ! application/x-rtp,encoding-name=H265',
            'rtph265depay ! h265parse ! avdec_h265',
            'decodebin ! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
            'appsink name=mysink emit-signals=true sync=false async=false max-buffers=2 drop=true',
        ])

        (system, target) = await self.find_gimbal()

        gimbal = self.gimbal_client
        time.sleep(0.1)
        gimbal.set_target(system, target)

        cv2.namedWindow('Gimbal', cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow('Gimbal', width, height)

        NAN = float("nan")

        print('Initialising stream...')

        gimbal_pipeline = GstVideoSource(GIMBAL_PIPELINE, leaky=True)
        gimbal_pipeline.startup()

        # while not self.exit_event.is_set():
        #     buffer = pipeline.pop()
        #     if buffer:
        #         break
        #     waited += 1
        #     print('\r  Frame not available (x{})'.format(waited), end='')
        #     cv2.waitKey(30)
        #     await asyncio.sleep(0.01)
        #
        # print('\nSuccess!\nStarting streaming - press "q" to quit.')
        # # ret, (width, height) = gst_utils.get_buffer_size_from_gst_caps(Gst.Caps)
        count = 0
        # gimbal_speed = 40
        while not self.exit_event.is_set():
            buffer = gimbal_pipeline.pop(timeout=0.01)
            count += 1
            # print(f" {count = }")
            await asyncio.sleep(0.001)
            # continue

            if buffer:
                cv2.imshow('Gimbal', buffer.data)

            k = cv2.waitKey(1)
            if k == ord('q') or k == ord('Q') or k == 27:
                break

            if k == ord('d'):  # Right arrow key
                print("Right arrow key pressed")
                await gimbal.set_attitude(NAN, NAN, 0.0, 0.2)
                # pan_tilt(gimbal_speed)
                KeyReleaseThread().start()

            if k == ord('a'):  # Left arrow key
                print("Left arrow key pressed")
                await gimbal.set_attitude(NAN, NAN, 0.0, -0.2)
                KeyReleaseThread().start()

            if k == ord('w'):
                print("Up arrow key pressed")
                await gimbal.set_attitude(NAN, NAN, 0.2, 0.0)
                KeyReleaseThread().start()

            if k == ord('s'):
                print("Down arrow key pressed")
                await gimbal.set_attitude(NAN, NAN, -0.2, 0.0)
                KeyReleaseThread().start()

            if k == ord('1'):
                print("Zoom in pressed")
                await gimbal.set_zoom(1)

            if k == ord('2'):
                print("Zoom out pressed")
                await gimbal.set_zoom(2)

            if k == ord('3'):
                print("Zoom stop pressed")
                await gimbal.set_zoom(3)

            if k == ord('4'):
                print("Zoom  = 1")
                await gimbal.set_zoom(4)

            if k == ord('5'):
                print("Zoom x2 in")
                await gimbal.set_zoom(5)

            if k == ord('6'):
                print("Zoom x2 out")
                await gimbal.set_zoom(6)

            if k == ord('c'):
                print("Snapshot in pressed")
                gimbal.start_capture()

        print("Gimbal View exit")
        # this cause errors perhaps because not running gst context
        #     gimbal_pipeline.pause()
        #     gimbal_pipeline.shutdown()


if __name__ == '__main__':

    btn_manager = ButtonManager()


    async def main():
        comp = 0
        window = create_window()
        btn_tasks = []
        while True:
            event, values = window.read(timeout=100)
            if event != '__TIMEOUT__':
                print(event, values)
                print(event, values)
                btn = btn_manager.find_button(event)
                task = btn.run_task() if btn else None
                if task: btn_tasks.append(task)

            if event == None or event == "Exit":
                for task in btn_tasks:
                    task.cancel()
                # self.exit_event.set()
                break

            elif event == 'Add Control Panel':
                comp += 1
                buttons = [FButton(None, comp, snapshot_task, 'Snapshot'),
                           FButton(None, comp, stream_task, 'Stream'),
                           FButton(None, comp, record_task, 'Record')]

                add_camera(None, window, btn_manager, comp, buttons=buttons)

            await asyncio.sleep(0.1)

        window.close()


    async def main2():
        def auto():
            print("Yay auto done")

        def reset():
            print("Yay reset done")

        def pause():
            print("Yay pause done")

        gui = Gui(auto=auto, reset=reset, pause=pause)

        # t1 = asyncio.create_task(gui.find_cameras())
        t2 = asyncio.create_task(gui.run_gui())

        try:
            await asyncio.gather(t2)
        except asyncio.CancelledError:
            print("CancelledError")
            pass


    # Run the main function using asyncio.run
    asyncio.run(main2())
