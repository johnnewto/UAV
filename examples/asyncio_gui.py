from typing import List

import PySimpleGUI as sg
import asyncio


class Btn_State:
    """ States of the button that executes a function and awaits the result """
    RUNNING=1
    READY=0
    DONE=2
    FAILED=3
    CANCELLED=4

print( f'{Btn_State.RUNNING = }')


async def proto_task(client:any, # mav component
                        comp: int = 22,  # server component ID (camera ID)
                        start:bool=True, # start or stop
                        timeout=5.0): # timeout
    yield Btn_State.RUNNING
    await asyncio.sleep(timeout)


class FButton:
    """ A class to manage a button that executes a function and awaits the result """

    def __init__(self, client, comp:int, function:proto_task, button_text:str):
        self.client = client
        self.comp = comp
        self.function:proto_task = function
        self.button_text = button_text
        self.key = f'{self.button_text}_{comp}'

        self.button_color = 'white on green'
        self.state = Btn_State.READY
        self.button = sg.Button(button_text = self.button_text, key = f'{self.button_text}_{comp}', button_color = self.button_color)

    def __repr__(self):
        return f'FunctionButton({self.button.key})'

    def __str__(self):
        return f'FunctionButton({self.button.key})'

    def set_state(self, state:int):
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

    #
    # async def handle_event(self, event, start, timeout=3):
    #     if event == self.key:
    #         async for state in self.function(self.gcs, start=start, timeout=timeout):
    #             self.set_state(state[0])

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

    # def find_handler(self, event):
    #     for button in self.buttons:
    #         if event == button.key:
    #             return button.handle_event
    #     return None

class ControlPanel:
    def __init__(self, comp, buttons=None):
        self.name= f'CP-{comp}'
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


def create_window(layout = None):
    """ Create a base layout and window"""
    if layout is None:
        layout = [
            # [
            [sg.Button('Add Control Panel'), sg.B('Cancel'), sg.Button('Exit')],
            # panel.get_layout(),
        ]
    window = sg.Window('Extend Layout Example', layout)
    return window

if __name__ == '__main__':
    async def snapshot_task(client, start=True, comp=22, timeout=5):
        if start:
            print(f'!!!Run the task {snapshot_task.__name__} _asyncio.sleep({timeout=}) ')
            ret = await client.image_start_capture(222, 22, interval=1, count=10)
        else:
            print(f'Cancel the task {snapshot_task.__name__} _asyncio.sleep({timeout=}) ')
            ret =  await client.image_stop_capture(222, 22)


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
            # await asyncio.sleep(1)
        # await asyncio.sleep(5)
        yield Btn_State.READY, "f{snapshot_func.__name__} Ready"


    async def _snapshot_task(client, button=None, run=True, timeout=5):
        if run:
            print(f'Run the {button = } {button.state = } task {_snapshot_task.__name__} _asyncio.sleep({timeout=}) ')
        else:
            print(f'Cancel the {button = } task {_snapshot_task.__name__} _asyncio.sleep({timeout=}) ')

        # print (f'{button.state = }, button_color = {button.button_color}, {button.key = }')

        await asyncio.sleep(timeout)
        return Btn_State.FAILED, "f{snapshot_func.__name__} Failed"

    async def stream_task(client, button=None, run=True, timeout=5):
        if run:
            print(f'Run the {button = } {button.state = } task {stream_task.__name__} asyncio.sleep({timeout=}) ')
            await asyncio.sleep(timeout)
            return Btn_State.RUNNING, "f{stream_func.__name__} RUNNING"
        else:
            print(f'Stop the {button = } {button.state = }  task {stream_task.__name__} asyncio.sleep({timeout=}) ')
            await asyncio.sleep(timeout)
            return Btn_State.READY, "f{stream_func.__name__} Stopped"

    async def record_task(button=None, run=True, timeout=5):
        print(f'executing the {button = } task {record_task.__name__} asyncio.sleep({timeout=}) ')
        print (f'{button.state = }, button_color = {button.button_color}, {button.key = }')
        await asyncio.sleep(timeout)
        return Btn_State.DONE, "f{record_func.__name__} Done"


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

    # Run the main function using asyncio.run
    asyncio.run(main())
