import asyncio
import time

from UAV.camera.gst_cam import GSTCamera
from UAV.logging import LogLevels
# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
from UAV.manager import Gui
from UAV.mavlink import CameraClient, CameraServer, MAVCom, mavlink
from UAV.utils import helpers
from UAV.utils.general import boot_time_str, toml_load, config_dir
from gstreamer import GstContext

def auto():
    print("Running auto")

async def main():
    con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
    # logger.disabled = True
    print(f"{boot_time_str =}")

    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread

        # with GstPipes(display_pipelines): # this will show the video on fpsdisplaysink
        with MAVCom(con1, source_system=111, loglevel=LogLevels.CRITICAL) as GCS_client:  # This normally runs on GCS
            with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server:  # This normally runs on drone

                # add GCS manager
                gcs: CameraClient = GCS_client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=LogLevels.INFO))

                # add UAV cameras, This normally runs on drone
                cam_1 = GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_0.toml"), loglevel=LogLevels.DEBUG)
                cam_2 = GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_1.toml"), loglevel=LogLevels.DEBUG)
                UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_1, loglevel=LogLevels.DEBUG))
                UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA2, camera=cam_2, loglevel=LogLevels.DEBUG))

                ret = await gcs.wait_heartbeat(target_system=222, target_component=22, timeout=1)
                print(f"Heartbeat {ret = }")
                #
                # await gcs.video_start_streaming(222, mavlink.MAV_COMP_ID_CAMERA, )
                # time.sleep(2)
                # await gcs.video_stop_streaming(222, mavlink.MAV_COMP_ID_CAMERA, )

                # Run the main function using asyncio.run
                gui = Gui(client=gcs, auto=auto)

                t1 = asyncio.create_task(gui.find_cameras())
                t2 = asyncio.create_task(gui.run_gui())

                try:
                    await asyncio.gather(t1, t2)
                except asyncio.CancelledError:
                    print("CancelledError")
                    pass
                cam_1.close()
                cam_2.close()


if __name__ == '__main__':
    p = helpers.start_displays(display_type='cv2', num_cams=2, port=5000)
    asyncio.run(main())
    p.terminate()
