import asyncio
import time

from UAV.cameras.gst_cam import GSTCamera
from UAV.gimbals.airsim_gimbal import AirsimGimbal
from UAV.gimbals.gimbal import Gimbal
from UAV.logging import LogLevels
# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
from UAV.manager import Gui
from UAV.mavlink import CameraClient, CameraServer, MAVCom, mavlink, GimbalManagerClient, GimbalServer
from UAV.utils import helpers
from UAV.utils.general import boot_time_str, toml_load, config_dir
from gstreamer import GstContext

def auto():
    print("Running auto")



async def main():
    con1, con2 = "udpin:localhost:14445", "udpout:localhost:14445"
    # con1, con2 = "/dev/ttyACM0", "/dev/ttyUSB1"
    # con1, con2 = "/dev/ttyACM0", "/dev/ttyACM2"
    # logger.disabled = True
    print(f"{boot_time_str =}")

    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread

        # with GstPipes(display_pipelines): # this will show the video on fpsdisplaysink
        with MAVCom(con1, source_system=111, loglevel=LogLevels.CRITICAL) as GCS_client:  # This normally runs on GCS
            with MAVCom(con2, source_system=222, loglevel=LogLevels.CRITICAL) as UAV_server:  # This normally runs on drone

                # add GCS manager
                gcs: CameraClient = GCS_client.add_component(CameraClient(mav_type=mavlink.MAV_TYPE_GCS, source_component=11, loglevel=LogLevels.DEBUG))
                # gcs_gim: GimbalManagerClient = GCS_client.add_component(GimbalManagerClient(mav_type=mavlink.MAV_TYPE_GIMBAL, source_component=12, loglevel=LogLevels.INFO))

                # add UAV cameras, This normally runs on drone
                cam_1 = GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_0.toml"), loglevel=LogLevels.DEBUG)
                cam_2 = GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_1.toml"), loglevel=LogLevels.DEBUG)

                UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA, camera=cam_1, loglevel=LogLevels.INFO))
                UAV_server.add_component(CameraServer(mav_type=mavlink.MAV_TYPE_CAMERA, source_component=mavlink.MAV_COMP_ID_CAMERA2, camera=cam_2, loglevel=LogLevels.INFO))
                # UAV_server.add_component(GimbalServer(mav_type=mavlink.MAV_TYPE_GIMBAL, source_component=mavlink.MAV_COMP_ID_GIMBAL, gimbal=gim_1, loglevel=LogLevels.DEBUG))

                # ret = await gcs.wait_heartbeat(target_system=222, target_component=mavlink.MAV_COMP_ID_CAMERA, timeout=4)
                ret = await gcs.wait_heartbeat(remote_mav_type=mavlink.MAV_TYPE_CAMERA, timeout=2)
                print(f"Camera Heartbeat {ret = }")
                # ret = await gcs.wait_heartbeat(remote_mav_type=mavlink.MAV_TYPE_GIMBAL, timeout=2)
                # print(f"GIMBAL Heartbeat {ret = }")
                #
                # await gcs.video_start_streaming(222, mavlink.MAV_COMP_ID_CAMERA, )
                # time.sleep(2)
                # await gcs.video_stop_streaming(222, mavlink.MAV_COMP_ID_CAMERA, )

                # ret = await gcs_gim.cmd_pitch_yaw(40, 0, 0, 0, 0, 0, 222, mavlink.MAV_COMP_ID_GIMBAL)
                #
                # gui = Gui(camera_client=gcs, gimbal_client=gcs_gim, auto=auto)
                gui = Gui(camera_client=gcs, gimbal_client=None, auto=auto)

                # Run the main function using asyncio.run
                t1 = asyncio.create_task(gui.find_cameras())
                # t2 = asyncio.create_task(gui.find_gimbals())
                t3 = asyncio.create_task(gui.run_gui())

                try:
                    # await asyncio.gather(t1, t2, t3)
                    await asyncio.gather(t1, t3)
                except asyncio.CancelledError:
                    print("CancelledError")
                    pass
                cam_1.close()
                cam_2.close()





if __name__ == '__main__':
    p = helpers.start_displays(display_type='cv2', num_cams=2, port=5000)
    asyncio.run(main())
    p.terminate()
