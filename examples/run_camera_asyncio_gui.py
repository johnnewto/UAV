
import asyncio
from dataclasses import dataclass

from asyncio_gui import Btn_State, FunctionButton, FunctionButtonManager, ControlPanel, create_window
from UAV.logging import LogLevels

from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil
from UAV.utils.general import boot_time_str

from UAV.camera import GSTCamera, read_camera_dict_from_toml
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

# async def test():
#     print ("test")
#     return True

async def snapshot_func(client, start=True, timeout=5):
    if start:
        print(f'!!!Run the task {snapshot_func.__name__} _asyncio.sleep({timeout=}) ')
        ret = await client.image_start_capture(222, 22, interval=1, count=5)
    else:
        print(f'Cancel the task {snapshot_func.__name__} _asyncio.sleep({timeout=}) ')
        ret =  await client.image_stop_capture(222, 22)
    print (f"{ret = }")
    if ret and start:
        return Btn_State.RUNNING, "f{snapshot_func.__name__} Running"
    elif ret and not start:
        return Btn_State.READY, "f{snapshot_func.__name__} Ready"
    else:
        return Btn_State.FAILED, "f{snapshot_func.__name__} Failed"


async def stream_func(client, start=True, timeout=5):
    if start:
        print(f'!!!Run the task {stream_func.__name__} asyncio.sleep({timeout=}) ')
        ret = await client.video_start_streaming(222, 22)
        if ret:
            return Btn_State.RUNNING, "f{stream_func.__name__} RUNNING"
        else:
            return Btn_State.FAILED, "f{stream_func.__name__} FAILED"
    else:
        print(f'Stop the task {stream_func.__name__} asyncio.sleep({timeout=}) ')
        ret = await client.video_stop_streaming(222, 22)
        if ret:
            return Btn_State.READY, "f{stream_func.__name__} Ready"
        else:
            return Btn_State.FAILED, "f{stream_func.__name__} FAILED"


async def record_func(client, button=None, start=True, timeout=5):
    print(f'executing the task {record_func.__name__} asyncio.sleep({timeout=}) ')
    # print (f'{button.state = }, button_color = {button.button_color}, {button.key = }')
    await asyncio.sleep(timeout)
    return Btn_State.DONE, "f{record_func.__name__} Done"

def add_camera(client, window, manager, cam_num):
    # Instantiate ControlPanel and extend the window's layout with it
    panel = ControlPanel(cam_num, buttons=[ FunctionButton(client, cam_num, snapshot_func,'Snapshot'),
                                            FunctionButton(client, cam_num, stream_func,'Stream'),
                                            FunctionButton(client, cam_num, record_func,'Record')])

    layout = panel.get_layout()
    window.extend_layout(window, [layout])
    for b in panel.buttons:
        manager.register(b)
    return cam_num+1
#
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
        manager = FunctionButtonManager()
        window = create_window().finalize()
        cam_num = add_camera(self.client, window, manager, 0)

        while True:
            # get
            try:
                # item = await self.new_cam_queue.get_nowait()
                item = self.new_cam_queue.get_nowait()
                print(f"Get Queue New camera {item = }")
                cam_num = add_camera(self.client, window, manager, cam_num)
            except asyncio.QueueEmpty:
                pass

            event, values = window.read(timeout=1)
            if event == '__TIMEOUT__':
                await asyncio.sleep(0.1)
            else:
                print(event, values)
                await manager.handle_event(event, window)

            if event == None or event == "Exit":
                self.exit_event.set()
                break

            elif event == 'Cancel':
                self.client.image_stop_capture(222, 22)
                for button in manager.buttons:
                    button.cancel_task()

                window[event].update('New Snap Text')

            elif event == 'Add Control Panel':
                cam_num = add_camera(self.client, window, manager, cam_num)
            await asyncio.sleep(0.1)

        window.close()
        print("run_gui exit")


async def main():

    # logger.disabled = True
    print (f"{boot_time_str =}")
    config_path = Path("../config")
    with GstContext(loglevel=LogLevels.INFO):  # GST main loop in thread
        with GstPipeline(GCS_DISPLAY_PIPELINE, loglevel=LogLevels.CRITICAL) as rcv_pipeline: # this will show the video on fpsdisplaysink
            # rcv_pipeline.log.disabled = True
            with MAVCom(con1, source_system=111, loglevel=LogLevels.CRITICAL) as GCS_client: # This normally runs on GCS
                with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server: # This normally runs on drone

                    # add GCS manager
                    gcs:CameraClient = GCS_client.add_component( CameraClient(mav_type=mavutil.mavlink.MAV_TYPE_GCS, source_component=11, loglevel=LogLevels.INFO))
                    # gcs.log.disabled = True
                    # add UAV cameras, This normally runs on drone
                    cam_1 = GSTCamera(camera_dict=read_camera_dict_from_toml(config_path / "test_camera_info.toml"), loglevel=LogLevels.INFO)
                    UAV_server.add_component(CameraServer(mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, source_component=22, camera=cam_1, loglevel=LogLevels.INFO))
                    # Run the main function using asyncio.run
                    gui = Gui(client=gcs)

                    t1 = asyncio.create_task(gui.find_cameras())
                    # asyncio.create_task(gui.find_cameras(gcs))
                    t2 = asyncio.create_task(gui.run_gui())
                    # g.fc = asyncio.create_task(find_cameras(gcs))

                    print("before gather")
                    try:
                        await asyncio.gather(t1, t2)
                    except asyncio.CancelledError:
                        print("CancelledError")
                        pass
                    # except Exception as e:
                    #     print("Exception", e)
                    #     pass
                    # finally:
                    #     print("finally")
                    #     gui.fc.cancel()



if __name__ == '__main__':
    asyncio.run(main())