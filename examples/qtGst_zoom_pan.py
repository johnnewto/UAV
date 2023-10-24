import sys
import time

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtGui import QCloseEvent
from gstreamer import GstPipeline, Gst, GstContext, GstPipes, GstXvimageSink, LogLevels
from gstreamer.utils import to_gst_string

from PyQt5.QtCore import Qt
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GstVideo, GstApp


class VideoWidget(QMainWindow):
    def __init__(self, test=False):
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

        if test:
            self.run_test_src()
            # time.sleep(0.1)
        self.init_ui()
        self.init_gstreamer()

        self.probeButton.clicked.connect(self.pipeline.set_probe_callback)


        self.pipeline.startup()

        # time.sleep(0.1)


        self.videobox = self.pipeline.get_by_name('videobox')
        self.src = self.pipeline.get_by_name('src')


    def init_gstreamer(self):

        Gst.init(None)

        # Initialize GStreamer pipeline
        command = to_gst_string(['videotestsrc name=src', 'videobox name=videobox', 'xvimagesink'])
        command = to_gst_string([
            'udpsrc port=5000 name = src ! application/x-rtp, media=video, clock-rate=90000, encoding-name=H264, payload=96',
            'queue',
            'rtph264depay ! avdec_h264',
            'videoconvert name = videoconv0',
            'videobox name=videobox',
            'videoconvert',
            # 'queue',
            'xvimagesink sync=false'
        ])
        # SINK_PIPELINE = to_gst_string([
        #     'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
        #     'rtph264depay ! avdec_h264',
        #     'xvimagesink sync=false',
        #     # 'autovideosink',
        # ])
        self.video_height = 480
        self.video_width = 640

        self.pipeline = GstXvimageSink(command=command, window_handle=self.window_handle, probe_width_height=self.probe_callback , loglevel=10)


    def probe_callback(self, width, height):
        self.video_width = width
        self.video_height = height
        print(f"Video dimensions: {width}x{height}")


    def init_ui(self):

        self.setWindowTitle('Zoom Video')
        self.probeButton = QPushButton(self)
        vbox = QVBoxLayout()
        self.video_widget = QWidget(self)
        vbox.addWidget(self.video_widget)
        vbox.addWidget(self.probeButton)
        container = QWidget(self)
        container.setLayout(vbox)
        self.setCentralWidget(container)

        # Setting up video output to our QWidget
        print('Setting up window_handle')
        self.window_handle = self.video_widget.winId()


        self.setGeometry(100, 100, 800, 600)




    def get_video_dimensions(self):
        """ Get the video dimensions from the caps of the src element"""
        try:
            self.pipeline.set_probe_callback()
        except:
            pass



    def closeEvent(self, event: QCloseEvent):
        try:
            # may not exist
            self.test_src_pipeline.shutdown()
        except:
            pass
        self.pipeline.shutdown()
        event.accept()

    def wheelEvent(self, event):
        degrees = event.angleDelta().y() / 8
        steps = degrees / 15
        self.zoom_level += 0.1 if steps > 0 else -0.1
        self.zoom_level = max(0.2, min(5.0, self.zoom_level) ) # Ensure zoom level isn't less than 1
        self.adjust_videobox()

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        self.get_video_dimensions()



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
        try:
            self.zoom_width = self.video_width * self.zoom_level
            self.zoom_height = self.video_height * self.zoom_level


            self.zoom_left = self.pan_x * self.video_width - self.zoom_width//2
            self.zoom_right = self.video_width -(self.zoom_left + self.zoom_width)

            self.zoom_top = self.pan_y * self.video_height - self.zoom_height//2
            self.zoom_bottom = self.video_height -(self.zoom_top + self.zoom_height)

             # print(f"{self.zoom_level = :3f    } {self.pan_x = :3f} {self.pan_y =:3f} {self.zoom_left =} {self.zoom_right =} {self.zoom_width =}")

            self.videobox.set_property('left', self.zoom_left)
            self.videobox.set_property('right', self.zoom_right)
            self.videobox.set_property('top', self.zoom_top)
            self.videobox.set_property('bottom', self.zoom_bottom)
        except AttributeError as e:
            print(f"AttributeError: {e}")
    def run_test_src(self, num_cams=2, udp_encoder='h264'):
        """ Test src pipeline"""
        SRC_PIPELINE = to_gst_string([
            # 'videotestsrc pattern=ball is-live=true num-buffers=1000 ! video/x-raw,framerate=20/1 ! tee name=t',
            'videotestsrc is-live=true  ! video/x-raw,format=I420, width=640,height=480,framerate=20/1',
            'x264enc tune=zerolatency',
            'rtph264pay ! udpsink host=127.0.0.1 port=5000',

        ])
        self.test_src_pipeline = GstPipeline(SRC_PIPELINE).startup()
        # with GstPipeline(SRC_PIPELINE) as pipeline:
        #     while pipeline.is_active:
        #         time.sleep(0.1)


# from gstreamer.utils import to_gst_string
# from gstreamer import GstPipeline, Gst, GstContext, GstPipes, GstReceiveUDP, LogLevels

SRC_PIPELINE = to_gst_string([
            # 'videotestsrc pattern=ball is-live=true num-buffers=1000 ! video/x-raw,framerate=20/1 ! tee name=t',
            'videotestsrc is-live=true num-buffers=1000 ! video/x-raw,format=I420, width=640,height=480,framerate=20/1',
            'tee name=t',
            't.',
            'queue leaky=2',
            # 'video/x-raw,format=I420,width=640,height=480',
            # 'textoverlay text="Frame: " valignment=top halignment=left shaded-background=true',
            # 'timeoverlay valignment=top halignment=right shaded-background=true',

            # 'videoconvert',
            # 'x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast',
            'x264enc tune=zerolatency',
            'rtph264pay ! udpsink host=127.0.0.1 port=5000',
            't.',
            'queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=5/1,format=(string)BGR',
            'videoconvert ! appsink name=mysink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
        ])

SINK_PIPELINE = to_gst_string([
            'udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
            'rtph264depay ! avdec_h264',
            'xvimagesink sync=false',
            # 'autovideosink',
        ])

def run_src(num_cams=2, udp_encoder='h264'):
    num_buffers = 40

    # with GstVideoSource(SRC_PIPELINE, leaky=True) as pipeline:
    with GstPipeline(SRC_PIPELINE) as pipeline:
        while pipeline.is_active:
            time.sleep(0.1)


        buffers = []
        count = 0
        dropstate = False
        while len(buffers) < num_buffers:
            time.sleep(0.1)
            # count += 1
            # if count % 10 == 0:
            #     print(f'Count = : {count}')
            #     dropstate = not dropstate
            #     pipeline.set_valve_state("myvalve", dropstate)
            buffer = pipeline.pop()
            if buffer:
                buffers.append(buffer)
                if len(buffers) % 10 == 0:
                    print(f'Got: {len(buffers)} buffers of {pipeline.queue_size}')
        print('Got: {} buffers'.format(len(buffers)))






if __name__ == '__main__':

    # num_buffers = 40
    # with GstPipeline(SINK_PIPELINE) as rcv_pipeline:
    #     with GstVideoSource(SRC_PIPELINE, leaky=True) as pipeline:
    #         buffers = []
    #         count = 0
    #         dropstate = False
    #         while len(buffers) < num_buffers:
    #             time.sleep(0.1)
    #             count += 1
    #             if count % 10 == 0:
    #                 print(f'Count = : {count}')
    #                 dropstate = not dropstate
    #                 pipeline.set_valve_state("myvalve", dropstate)
    #             buffer = pipeline.pop()
    #             if buffer:
    #
    #                 buffers.append(buffer)
    #                 if len(buffers) % 10 == 0:
    #                     print(f'Got: {len(buffers)} buffers of {pipeline.queue_size}')
    #         print('Got: {} buffers'.format(len(buffers)))

    from multiprocessing import Process
    #
    # p1 = Process(target=run_src,)   #  todo put this into the app  fix no caps
    # p2 = Process(target=run_sink,)
    #
    # p1.start()
    # starting process 2
    # p2.start()
    # p1.join()
    # sys.exit(0)
    # test_src_pipeline = GstPipeline(SRC_PIPELINE).startup()
    app = QApplication(sys.argv)
    window = VideoWidget(test=True)
    window.show()
    # app.exec_()
    sys.exit(app.exec_())

    # p1.join()
