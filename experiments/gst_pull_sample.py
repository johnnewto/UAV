import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
import cv2
import numpy as np

# Initialize GStreamer
Gst.init(None)

# Create a pipeline
pipeline = Gst.parse_launch("videotestsrc ! videoconvert ! appsink name=sink")

# Get the sink element from the pipeline
appsink = pipeline.get_by_name("my_sink")

# Make sure the pipeline is playing to get samples
pipeline.set_state(Gst.State.PLAYING)

def pull_and_show_sample():
    # Pull sample
    sample = appsink.emit("pull-sample")

    if sample:
        # Convert GstSample to numpy array
        buf = sample.get_buffer()
        caps = sample.get_caps()
        array = np.ndarray(
            (caps.get_structure(0).get_value("height"),
             caps.get_structure(0).get_value("width"), 3),
            buffer=buf.extract_dup(0, buf.get_size()),
            dtype=np.uint8)

        # Convert from BGR to RGB (OpenCV uses BGR by default)
        array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
        print("sample")
        # Show image using OpenCV
        cv2.imshow("Frame", array)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            pipeline.set_state(Gst.State.NULL)
            cv2.destroyAllWindows()

    return True  # Keep the function attached to the timeout

# Continuously pull samples and show them
GObject.timeout_add(330, pull_and_show_sample)  # 33 milliseconds timeout (approx 30 fps)

# Start main loop
loop = GObject.MainLoop()
try:
    loop.run()
except:
    pass




# import gi
# gi.require_version('Gst', '1.0')
# from gi.repository import Gst, GObject, GLib
#
# # Initialize GStreamer
# Gst.init(None)
#
# # Create a pipeline
# pipeline = Gst.parse_launch("videotestsrc ! videoconvert ! appsink name=my_sink")
#
# # Get the sink element from the pipeline
# appsink = pipeline.get_by_name("my_sink")
#
# # Run the pipeline
# pipeline.set_state(Gst.State.PLAYING)
#
# def pull_sample():
#     sample = appsink.emit("pull-sample")
#     if sample:
#         print("Sample pulled:", sample)
#     else:
#         print("Could not pull sample")
#
# def gst_to_opencv(sample):
#     "Transform byte array into np array"
#     if sample is None:
#         return None
#     buf = sample.get_buffer()
#     caps_structure = sample.get_caps().get_structure(0)
#     array = np.ndarray(
#         (caps_structure.get_value('height'), caps_structure.get_value('width'), 3),
#         buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
#     return array
#
# def get_image( camera_id):
#     sample = pull_sample(camera_id)
#     return gst_to_opencv(sample)
# # After the pipeline is playing, pull a sample
#
# GLib.timeout_add(500, pull_sample)  # Call pull_sample() after 500 ms
#
# # Start main loop
# loop = GLib.MainLoop()
# try:
#     loop.run()
#
# except:
#     pass
#
# import gi
# gi.require_version('Gst', '1.0')
# from gi.repository import Gst, GObject
#
# # Initialize GStreamer
# Gst.init(None)
#
# # Create a pipeline
# pipeline = Gst.parse_launch("videotestsrc ! videoconvert ! appsink name=my_sink")
#
# # Get the sink element from the pipeline
# appsink = pipeline.get_by_name("my_sink")
#
# # Run the pipeline
# pipeline.set_state(Gst.State.PLAYING)
#
# def pull_sample():
#     sample = appsink.emit("pull-sample")
#     if sample:
#         print("Sample pulled:", sample)
#     else:
#         print("Could not pull sample")
#
# # After the pipeline is playing, pull a sample
# GObject.timeout_add(500, pull_sample)  # Call pull_sample() after 500 ms
#
# # Start main loop
# loop = GObject.MainLoop()
# try:
#     loop.run()
# except:
#     pass
# In this example, videotestsrc generates test video data, which is then converted using videoconvert before reaching the appsink (named my_sink). The pull_sample() function pulls a sample from the sink using emit('pull-sample').
#
# Note: You should run this example in an environment where GStreamer and its Python bindings are installed.
#
#
#
#
# User
# can you add cv2 showimage
# ChatGPT
# Certainly! To integrate OpenCV (cv2) with GStreamer's appsink, you can pull video frames and display them using OpenCV's imshow function. Here's a modified example that pulls a sample from appsink, converts it to an OpenCV image, and then displays it using cv2.imshow().
#
# Firstly, make sure you have OpenCV installed. If you haven't installed it yet, you can install it via pip:
#
# Copy code
# pip install opencv-python
# Then, you can use the following code:
#
# python
# Copy code
# import gi
# gi.require_version('Gst', '1.0')
# from gi.repository import Gst, GObject
# import cv2
# import numpy as np
#
# # Initialize GStreamer
# Gst.init(None)
#
# # Create a pipeline
# pipeline = Gst.parse_launch("videotestsrc ! videoconvert ! appsink name=my_sink")
#
# # Get the sink element from the pipeline
# appsink = pipeline.get_by_name("my_sink")
#
# # Make sure the pipeline is playing to get samples
# pipeline.set_state(Gst.State.PLAYING)
#
# def pull_and_show_sample():
#     # Pull sample
#     sample = appsink.emit("pull-sample")
#
#     if sample:
#         # Convert GstSample to numpy array
#         buf = sample.get_buffer()
#         caps = sample.get_caps()
#         array = np.ndarray(
#             (caps.get_structure(0).get_value("height"),
#              caps.get_structure(0).get_value("width"), 3),
#             buffer=buf.extract_dup(0, buf.get_size()),
#             dtype=np.uint8)
#
#         # Convert from BGR to RGB (OpenCV uses BGR by default)
#         array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
#
#         # Show image using OpenCV
#         cv2.imshow("Frame", array)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             pipeline.set_state(Gst.State.NULL)
#             cv2.destroyAllWindows()
#
#     return True  # Keep the function attached to the timeout
#
# # Continuously pull samples and show them
# GObject.timeout_add(33, pull_and_show_sample)  # 33 milliseconds timeout (approx 30 fps)
#
# # Start main loop
# loop = GObject.MainLoop()
# try:
#     loop.run()
# except:
#     pass
#
