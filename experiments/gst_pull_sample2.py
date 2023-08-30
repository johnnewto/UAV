import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import cv2
import numpy as np

# Initialize GStreamer
Gst.init(None)


# Callback to be called when a new sample is ready at the sink
def new_sample(sink):
    # Pull new sample from sink
    sample = sink.emit("pull-sample")

    # Convert GstSample to numpy array
    buf = sample.get_buffer()
    caps_structure = sample.get_caps().get_structure(0)
    array = np.ndarray(
        (caps_structure.get_value('height'), caps_structure.get_value('width'), 3),
        buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)

    # Convert to RGB (OpenCV uses BGR by default)
    array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
    print(array.shape)

    # # Show image using OpenCV
    # cv2.imshow("Frame", array)
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     cv2.destroyAllWindows()
    #     loop.quit()

    # buffer.unmap(info)
    return Gst.FlowReturn.OK



# Create a pipeline
pipeline = Gst.parse_launch("videotestsrc ! videoconvert ! appsink name=my_sink")
pipeline2 = Gst.parse_launch("videotestsrc ! videoconvert ! autovideosink")

# Get the sink element from the pipeline
appsink = pipeline.get_by_name("my_sink")
# Enable new-sample signal emission (important!)
appsink.set_property("emit-signals", True)
# appsink.connect("new-sample", new_sample)


# Start playing
pipeline.set_state(Gst.State.PLAYING)
pipeline2.set_state(Gst.State.PLAYING)


GLib.timeout_add(500, pull_sample)

# Create GLib loop
loop = GLib.MainLoop()
print("started")
try:
    loop.run()
except:
    print("error")
    pass

# Stop pipeline
pipeline.set_state(Gst.State.NULL)
pipeline2.set_state(Gst.State.NULL)