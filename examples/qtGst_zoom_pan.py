"""
https://brettviren.github.io/pygst-tutorial-org/pygst-tutorial.html

"""


import sys
import time

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtCore import Qt
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GstVideo


class VideoWidget(QMainWindow):
    def __init__(self):
        super().__init__()



        # Zoom and pan state
        self.zoom_level = 1.0
        self.pan_x = 0.5
        self.pan_y = 0.5
        self.left_crop = 0
        self.right_crop = 0
        self.top_crop = 0
        self.bottom_crop = 0

        self.last_mouse_pos = None

        self.init_gstreamer()
        self.init_ui()
        self.start_pipeline()

    def init_gstreamer(self):
        Gst.init(None)


        # Initialize GStreamer pipeline
        self.pipeline = Gst.Pipeline()
        self.src = Gst.ElementFactory.make('videotestsrc', None)

        self.src = Gst.ElementFactory.make('videotestsrc', None)

        self.videobox = Gst.ElementFactory.make('videobox', None)
        self.sink = Gst.ElementFactory.make('xvimagesink', None)

        # Add elements to the pipeline and link them
        self.pipeline.add(self.src)
        self.pipeline.add(self.videobox)
        self.pipeline.add(self.sink)
        self.src.link(self.videobox)
        self.videobox.link(self.sink)


        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        # bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
        self.bus.connect('message::error', self.on_error)
        self.bus.connect('sync-message::element', self.on_sync_message)



    def init_ui(self):

        self.setWindowTitle('Zoom Video')
        layout = QVBoxLayout()
        self.video_widget = QWidget(self)
        layout.addWidget(self.video_widget)
        container = QWidget(self)
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Setting up video output to our QWidget
        print('Setting up window_handle')
        self.window_handle = self.video_widget.winId()

        self.setGeometry(100, 100, 800, 600)


    def start_pipeline(self):
        # ... your existing pipeline setup code ...

        self.pipeline.set_state(Gst.State.PLAYING)
        print('todo ???? Wait awhile for state change to playing')  # todo fixme
        time.sleep(0.1)
        print('Getting video dimensions')
        pad = self.src.get_static_pad("src")
        cap = pad.get_current_caps()
        if cap:
            struct = cap.get_structure(0)
            self.video_width = struct.get_int("width")[1]
            self.video_height = struct.get_int("height")[1]

    def on_error(self, bus, msg):
        print('Error:', msg.parse_error())

    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle')
            msg.src.set_window_handle(self.window_handle)
            # msg.src.set_window_handle(self.windowId)

    def closeEvent(self, event: QCloseEvent):
        self.pipeline.set_state(Gst.State.NULL)
        event.accept()

    def wheelEvent(self, event):
        degrees = event.angleDelta().y() / 8
        steps = degrees / 15
        self.zoom_level += 0.1 if steps > 0 else -0.1
        self.zoom_level = max(0.2, min(5.0, self.zoom_level) ) # Ensure zoom level isn't less than 1
        self.adjust_videobox()

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()



    def mouseMoveEvent(self, event):
        dx = (event.pos().x() - self.last_mouse_pos.x()) / self.width()
        dy = (event.pos().y() - self.last_mouse_pos.y()) / self.height()

        self.pan_x -= dx * self.zoom_level
        self.pan_y -= dy * self.zoom_level

        self.pan_x = max(0.0, min(1.0, self.pan_x))
        self.pan_y = max(0.0, min(1.0, self.pan_y))
        # print(f"{self.pan_x =}, {self.pan_y =} {self.zoom_level =} {self.video_width =}, {self.video_height =}, {self.width() =}, {self.height() =}")

        self.last_mouse_pos = event.pos()  # Update the last position
        self.adjust_videobox()

    def adjust_videobox(self):

        self.zoom_width = self.video_width * self.zoom_level
        self.zoom_height = self.video_height * self.zoom_level


        self.zoom_left = self.pan_x * self.video_width - self.zoom_width//2
        self.zoom_right = self.video_width -(self.zoom_left + self.zoom_width)

        self.zoom_top = self.pan_y * self.video_height - self.zoom_height//2
        self.zoom_bottom = self.video_height -(self.zoom_top + self.zoom_height)

        # print(f"{self.zoom_level = :3f} {self.pan_x = :3f} {self.pan_y =:3f} {self.zoom_left =} {self.zoom_right =} {self.zoom_width =}")

        self.videobox.set_property('left', self.zoom_left)
        self.videobox.set_property('right', self.zoom_right)
        self.videobox.set_property('top', self.zoom_top)
        self.videobox.set_property('bottom', self.zoom_bottom)




app = QApplication(sys.argv)
window = VideoWidget()
window.show()
sys.exit(app.exec_())
