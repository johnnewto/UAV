import time

import gstreamer.utils as gst_utils
from UAV.cameras.gst_cam import GSTCamera
from UAV.utils import start_displays
from UAV.utils.general import boot_time_str, toml_load, config_dir
from gstreamer import GstContext, Gst

gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
if __name__ == '__main__':
    print(f"{boot_time_str =}")
    p = start_displays(display_type='cv2', num_cams=2, port=5000)
    with GstContext():
        with GSTCamera(camera_dict=toml_load(config_dir() / "test_camera_special.toml"), loglevel=10) as cam:
            time.sleep(1)
            # p = start_displays(num_cams=2, port=5000)
            time.sleep(1)
            for i in range(100):
                cam.video_start_streaming()
                time.sleep(2)
                cam.video_stop_streaming()
                time.sleep(1)

            # cam.image_start_capture(0.1, 5)
            # while cam._gst_image_save.is_active:
            #     if cam.last_image is not None:
            #         pass
            #         cv2.imshow('image', cam.last_image)
            #         cam.last_image = None
            #     cv2.waitKey(10)
            # print(f"Waiting for capture thread to finish")
    try:
        p.terminate()
    except:
        pass
