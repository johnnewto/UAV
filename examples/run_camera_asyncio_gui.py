
import asyncio
import PySimpleGUI as sg

from UAV.logging import LogLevels

from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil, mavlink
from UAV.utils import helpers
from UAV.utils.general import boot_time_str, toml_load, config_dir

from UAV.camera.gst_cam import GSTCamera
from gstreamer import  GstPipeline, Gst, GstContext, GstPipes
from gstreamer.utils import to_gst_string
import time
from pathlib import Path
# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
from UAV.manager import Gui

async def main():
    con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
    # logger.disabled = True
    print (f"{boot_time_str =}")

    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread

        # with GstPipes(display_pipelines): # this will show the video on fpsdisplaysink
            with MAVCom(con1, source_system=111, loglevel=LogLevels.CRITICAL) as GCS_client: # This normally runs on GCS
                with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server: # This normally runs on drone

                    # add GCS manager
                    gcs:CameraClient = GCS_client.add_component( CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=LogLevels.INFO))

                    # add UAV cameras, This normally runs on drone
                    cam_1 = GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_0.toml"), loglevel=LogLevels.DEBUG)
                    cam_2 = GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_1.toml"), loglevel=LogLevels.DEBUG)
                    UAV_server.add_component( CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component= mavlink.MAV_COMP_ID_CAMERA, camera=cam_1, loglevel=LogLevels.DEBUG))
                    UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component= mavlink.MAV_COMP_ID_CAMERA2, camera=cam_2, loglevel=LogLevels.DEBUG))



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

    p = helpers.start_displays(num_cams=2, port=5000)
    asyncio.run(main())
    p.terminate()