import sys
import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, Gtk, Gdk, GstVideo
from gstreamer import utils as gst_utils
class VideoWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="GTK GL Sink Example")
        self.connect('destroy', Gtk.main_quit)

        # Initialize GStreamer
        Gst.init(None)


        # Build the GStreamer pipeline with gtkglsink
        self.pipeline = Gst.parse_launch("videotestsrc ! autovideoconvert ! gtkglsink name=sink")

        # Get the sink element and retrieve the widget
        self.sink = self.pipeline.get_by_name("sink")
        self.gl_area = self.sink.get_property("widget")

        if self.gl_area:
            self.add(self.gl_area)

        # Start playing the pipeline
        self.pipeline.set_state(Gst.State.PLAYING)

gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
if __name__ == "__main__":
    window = VideoWindow()
    window.show_all()
    Gtk.main()
