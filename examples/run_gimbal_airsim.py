import time

from UAV.cameras.airsim_cam import AirsimCamera
from UAV.gimbals.airsim_gimbal import AirsimGimbal
from UAV.logging import LogLevels
from UAV.utils import start_displays
from UAV.utils.general import toml_load, config_dir
from gstreamer import GstContext

# gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
if __name__ == '__main__':

    UDP_ENCODER = 'h264'
    # UDP_ENCODER = 'raw-video'
    camera_dict_0 = toml_load(config_dir() / "airsim_cam_front.toml")
    camera_dict_1 = toml_load(config_dir() / "airsim_cam_left.toml")

    p = start_displays(num_cams=2, port=5000)

    camera_name = '0'
    with GstContext():
        with AirsimCamera(camera_name='0', camera_dict=camera_dict_0, loglevel=LogLevels.INFO) as air_cam_0:
            # if True:
            with AirsimGimbal(camera_name='0', loglevel=10) as gimbal:
                air_cam_0.video_start_streaming()
                time.sleep(0.5)
                pitch = 0
                gimbal.set_pitch_yaw(pitch=0, yaw=180, pitchspeed=10, yawspeed=10)
                for i in range(36):
                    pitch = pitch + 10
                    gimbal.set_pitch_yaw(pitch=pitch, yaw=190, pitchspeed=10, yawspeed=10)
                    # gimbal.rotate_cam(pitch=10, yaw=0)
                    time.sleep(0.1)

            time.sleep(0.5)
            gimbal.set_pitch_yaw(pitch=0, yaw=0, pitchspeed=10, yawspeed=10)

    p.terminate()
    # for i in range(45):
    #     gimbal.set_pitch_yaw(pitch=45-i, yaw=90, pitchspeed=10, yawspeed=10)
    #     time.sleep(0.1)
    # air_cam_1.video_stop_streaming()
time.sleep(1)
print(f"Waiting for capture thread to finish")
