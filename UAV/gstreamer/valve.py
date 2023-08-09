# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/api/10_gstreamer.valve.ipynb.

# %% auto 0
__all__ = ['logger', 'DefaultParams', 'GstStream', 'ping_ip', 'Mqtt', 'main']

# %% ../../nbs/api/10_gstreamer.valve.ipynb 5
from fastcore.utils import *
from fastcore.utils import *
import cv2
import gi
import numpy as np
from imutils import resize
# from ping_ip import ping_ip
import threading
from multiprocessing import Process
from gi.repository import Gst
import subprocess
import platform

import paho.mqtt.client as mqtt_client

import time
# from dataloader import LoadImages, resize
from pathlib import Path
import logging
# import .nbs.Gstreamer.gst_parameters as params

# %% ../../nbs/api/10_gstreamer.valve.ipynb 6
logging.basicConfig(format='%(asctime)-8s,%(msecs)-3d %(levelname)5s [%(filename)10s:%(lineno)3d] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)  # Todo add this to params
logger = logging.getLogger(__name__)

# %% ../../nbs/api/10_gstreamer.valve.ipynb 7
# gi.require_version('Gst', '1.0')

# %% ../../nbs/api/10_gstreamer.valve.ipynb 10
#|code-fold: true
from dataclasses import dataclass

@dataclass
class DefaultParams():
    camera_dev = "CAM-0"
    cameras = {
        "CAM-0": {
            "gst": [
                'videotestsrc pattern=smpte is-live=true ! tee name=t ',
                't. ! queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=10/1,format=(string)BGR ! ',
                '   videoconvert ! appsink name=sink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
                't. ! queue leaky=2 ! valve name=myvalve drop=true ! video/x-raw,format=I420,width=640,height=480 ! videoconvert ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=5000',
                ],
            "udp": True,
            "host": "127.0.0.1",
            "port": 5000,
        },
        "CAM-1": {
            "gst": [
                'videotestsrc pattern=ball is-live=true ! tee name=t ',
                't. ! queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=10/1,format=(string)BGR ! ',
                '   videoconvert ! appsink name=sink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
                't. ! queue leaky=2 ! valve name=myvalve drop=true ! video/x-raw,format=I420,width=640,height=480 ! videoconvert ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=5001',
                ],
            "udp": True,
            "host": "127.0.0.1",
            "port": 5001,
        },
        "CAM-2": {
            "gst": [
                'videotestsrc pattern=snow is-live=true ! tee name=t ',
                't. ! queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=10/1,format=(string)BGR ! ',
                '   videoconvert ! appsink name=sink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
                't. ! queue leaky=2 ! valve name=myvalve drop=true ! video/x-raw,format=I420,width=640,height=480 ! videoconvert ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=5002',
                ],
            "udp": True,
            "host": "127.0.0.1",
            "port": 5002,
        },
        "CAM-3": {
            "gst": [
                'videotestsrc pattern=pinwheel is-live=true ! tee name=t ',
                't. ! queue leaky=2 ! videoconvert ! videorate drop-only=true ! video/x-raw,framerate=10/1,format=(string)BGR ! ',
                '  videoconvert ! appsink name=sink emit-signals=true  sync=false async=false  max-buffers=2 drop=true ',
                't. ! queue leaky=2 ! valve name=myvalve drop=true ! video/x-raw,format=I420,width=640,height=480 ! videoconvert ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=5003',
                ],
            "udp": True,
            "host": "127.0.0.1",
            "port": 5003,
            },
    
       }

    # socket address and port
    mqqt_address='127.0.0.1'
    src_port=1234

# %% ../../nbs/api/10_gstreamer.valve.ipynb 15
#| code-fold: true
# https://github.com/gkralik/python-gst-tutorial/blob/master/basic-tutorial-4.py

class GstStream():
    """"GstStream  class using gstreamer
        Create and start a GStreamer pipe
            gst_pipe = GstStream()
        """
    
    def __init__(self, name:str='CAM-0' # camera name
                 , gstcommand:List=['videotestsrc ! autovideosink'] # gst command list
                 , address:str='127.0.0.1'  # udp address
                 , port:int=5000): # udp port
        
        Gst.init(None)
        assert isinstance(name, str), "name must be a string"
        self.name = name
        assert isinstance(gstcommand, List), "gstcommand must be a list"
        self.gstcommand = gstcommand
        self.address = address
        self.port = port

        self.latest_frame = self._new_frame = None
        self.start_gst()
        self._thread = threading.Thread(target=self.msg_thread_func, daemon=True)
        self._stop_thread = False
        self._thread .start()
        logger.info("GstStream started")

    def start_gst(self):
        """ Start gstreamer pipeline and sink
        """
        if self.gstcommand != []:
            command = ' '.join(self.gstcommand)
        else:
            command = 'videotestsrc ! autovideosink'
            command = "videotestsrc ! tee name=t t. ! queue ! autovideosink " +\
                       " t. ! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert ! " +\
                       " queue ! appsink name=sink emit-signals=true "

        # print (command)
        self.pipeline = Gst.parse_launch(command)
        self.appsink = self.pipeline.get_by_name('sink')
        try:
            self.appsink.connect('new-sample', self.callback)
        except:
            logger.error("Error connecting to callback")
            
        self.pipeline.set_state(Gst.State.PLAYING)
        self.bus = self.pipeline.get_bus()
        
    def msg_thread_func(self):   
        "Run thread"
        # Poll for messages on the bus (like EOS or ERROR), and handle them
        while not self._stop_thread:
            message = self.bus.timed_pop_filtered(100*Gst.MSECOND, Gst.MessageType.ANY)
            if message is None:
                continue
    
            if message.type == Gst.MessageType.EOS:
                logger.info("End-Of-Stream reached.")
                break
            elif message.type == Gst.MessageType.ERROR:
                err, debug = message.parse_error()
                logger.error("JN Error received from element %s: %s" % (message.src.get_name(), err))
                logger.error("Debugging information: %s" % debug)
                break
        # Cleanup 
        logger.info("Stopping GstStream")
        self.pipeline.set_state(Gst.State.NULL)
        
    @staticmethod
    def gst_to_opencv(sample):
        "Transform byte array into np array"
        buf = sample.get_buffer()
        caps_structure = sample.get_caps().get_structure(0)
        array = np.ndarray(
            ( caps_structure.get_value('height'),caps_structure.get_value('width'), 3),
            buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
        return array

    def frame(self):
        """ Get Frame
        Returns:
            np.ndarray: latest retrieved image frame
        """
        if self.frame_available:
            self.latest_frame = self._new_frame
            # reset to indicate latest frame has been 'consumed'
            self._new_frame = None
        return self.latest_frame

    def frame_available(self, 
                             timeout=2  # timeout in seconds
                             )->bool:   # true if a new frame is available within timeout    
        """Wait for a new frame to be available"""
        elapsetime = 0
        while self._new_frame is None:
            time.sleep(0.01)
            elapsetime += 0.01
            if elapsetime > timeout:
                return False
        return True
    
            
    def callback(self, sink):
        sample = sink.emit('pull-sample')
        # if not self.pause:
        self._new_frame = self.gst_to_opencv(sample)

        return Gst.FlowReturn.OK
    
    def close(self):
        """Close gstreamer pipeline
        see https://github.com/gkralik/python-gst-tutorial/blob/master/basic-tutorial-1.py
        """
        self.pipeline.send_event(Gst.Event.new_eos())   # Todo does not seem to stop pipeline
        self.pipeline.set_state(Gst.State.NULL)
        self._stop_thread = True
        self._thread.join()
        logger.info("GstStream closed")

        
    def __enter__(self):
        """with context manager"""

        return self  # This value is assigned to the variable after 'as' in the 'with' statement
    
    def __exit__(self, exc_type, exc_value, traceback):
        """with context manager"""
        self.close()
        # If an exception occurred, exc_type, exc_value, and traceback will be provided
        # Returning False (or None) will propagate the exception
        # Returning True will suppress it
        return False


# %% ../../nbs/api/10_gstreamer.valve.ipynb 20
@patch     # patch will allow nbdev to document this function when running nbdev_build_docs
def toggle_valve_state(self:GstStream
                        , valvename: str):  # name of valve element
    " Toggle the state of a valve element"

    valve = self.pipeline.get_by_name(valvename)
    logger.info(f"{self.name}: current_drop_state: {current_drop_state}")
    valve.set_property("drop", not current_drop_state)
    current_drop_state = valve.get_property("drop")
    logger.info(f"{self.name}: new_drop_state: {current_drop_state}")

# %% ../../nbs/api/10_gstreamer.valve.ipynb 21
@patch
def set_valve_state(self:GstStream
                    , valvename: str  # name of valve element
                    , drop_state: bool  # True = drop frames
                    ):
    "Set the state of a valve element"

    valve = self.pipeline.get_by_name(valvename)
    valve.set_property("drop", drop_state)
    new_drop_state = valve.get_property("drop")
    logger.info(f"{self.name}: new drop state: {new_drop_state}")


# %% ../../nbs/api/10_gstreamer.valve.ipynb 22
@patch
def get_valve_state(self:GstStream
                    , valvename: str  # name of valve element
                    ):
    "Get the state of a valve element"

    valve = self.pipeline.get_by_name(valvename)
    return valve.get_property("drop")


# %% ../../nbs/api/10_gstreamer.valve.ipynb 26
def ping_ip(ip_address:str # IP address to ping
            )->bool :  # returns True if IP address is in use
    "Ping an IP address to see if it is in use"
    if platform.system().lower() == "windows":
        status = subprocess.call(
            ['ping', '-q', '-n', '1', '-W', '1', ip_address],
            stdout=subprocess.DEVNULL)
    else:
        status = subprocess.call(
            ['ping', '-q', '-c', '1', '-W', '1', ip_address],
            stdout=subprocess.DEVNULL)

    if status == 0:
        return True
    else:
        return False

# %% ../../nbs/api/10_gstreamer.valve.ipynb 30
class Mqtt:
    "Class to control a gst valve via MQTT"
    def __init__(self, camera:str  # name of camera
                 , video:GstStream  # video object
                 , valve_name:str="myvalve"  # name of valve element
                 , addr:str="127.0.0.1"  # IP address of MQTT broker
                 ):
        self.camera = camera
        self.video = video
        self.valve_name = valve_name
        self.client = mqtt_client.Client(self.camera)
        self.msg = None

        if ping_ip(addr):
            logger.info(f"Connecting to {addr}")
            self.client.connect(addr)
        else:
            logger.info("Connecting to 127.0.0.1")
            self.client.connect("127.0.0.1")

        self.client.loop_start()
        
        self.connected = False
        self.client.on_message = self.on_mqtt_message
        self.client.on_connect = self.on_connect


    def on_mqtt_message(self, client:mqtt_client.Client # mqtt client
                        , userdata # user data
                        , message:mqtt_client.MQTTMessage # message
                        ):
        """Callback function for mqtt_client message
            Sets the valve state to True or False depending on the message payload"""
        self.msg = str(message.payload.decode("utf-8"))
        logger.info(f"Received message: {self.msg}" )
        if self.video is not None:
            try:
                if self.msg == self.camera:
                    self.video.set_valve_state(self.valve_name, False)
                else:
                    self.video.set_valve_state(self.valve_name, True)
            except Exception as e:
                logger.error(f"Not able to set valve state: {e}")   # todo - log this error and fix it
    
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        """The callback for when the client receives a CONNACK response from the server."""
        logger.info("Connected with result code "+str(rc))
        self.client.subscribe("STREAM-CAMERA")
        self.connected = True
        
    def wait_connection(self, 
                             timeout=2  # timeout in seconds
                             )->bool:   # true if connected within timeout    
        """Wait for connection to be available"""
        elapsetime = 0
        while not self.connected:
            time.sleep(0.01)
            elapsetime += 0.01
            if elapsetime > timeout:
                logger.error("Mqtt: Timeout waiting for connection")
                return False
            
        return True
        
    def close(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Closed mqtt_client client")
        
    def __enter__(self):
        """with context manager"""
        return self  # This value is assigned to the variable after 'as' in the 'with' statement
    
    def __exit__(self, exc_type, exc_value, traceback):
        """with context manager"""
        self.close()
        # If an exception occurred, exc_type, exc_value, and traceback will be provided
        # Returning False (or None) will propagate the exception
        # Returning True will suppress it
        return False



# %% ../../nbs/api/10_gstreamer.valve.ipynb 34
#| code-fold: true
def main(camera="CAM-0"):
    params = DefaultParams()
    gstcommand = params.cameras[camera]["gst"]
    video = GstStream(camera, gstcommand)
    cv2.namedWindow(camera, cv2.WINDOW_NORMAL)
    mqtt = Mqtt(camera, video)

    logger.info('Initialising stream...')
    waited = 0
    while not video.frame_available():
        waited += 1
        print('\r  Frame not available (x{})'.format(waited), end='')
        cv2.waitKey(30)

    logger.info('\nSuccess!\nStarting streaming - press "q" to quit.')

    print ("Type q to stop")
    wait_time = 1
    count = 0
    while True:

        if video.frame_available() and count % 10 == 0:
            frame = video.frame().copy()
            # # cv2.putText(frame, f'{frame_num:2d} {data_received}', (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
            frame = resize(frame, width= 600)
            cv2.imshow(camera, frame)
            pass


        if count % 1000 == 0:
            print( count)
        count += 1


        k = cv2.waitKey(wait_time)

        if k == ord('q') or k == ord('Q') or k == 27:
            break

        if k == ord('v'):
            # Assuming you have a valve element named 'myvalve' in your pipeline
            valve = video.pipeline.get_by_name("myvalve")
            current_drop_state = valve.get_property("drop")
            print(f"current_drop_state {current_drop_state}")
            valve.set_property("drop", not current_drop_state)
            current_drop_state = valve.get_property("drop")
            print(f"new_drop_state {current_drop_state}", )

            time.sleep(2)

        if k == ord(' '):
            if wait_time != 0:
                wait_time = 0
            else:
                wait_time = 1

        if k == ord('s'):
            save = 0
            save_path = Path(params.save_path) 
            save_path.mkdir(exist_ok=True)
            pass

    mqtt.close()
    video.close()
    cv2.destroyAllWindows()
    logger.info("Closed all")
    

# %% ../../nbs/api/10_gstreamer.valve.ipynb 37
#|eval: false     don't run this cell in testing
#|code-fold: true
from multiprocessing import Process   # you will need to import Process from multiprocessing

if __name__ == '__main__':

    cams = []
    params = DefaultParams()
    for cam in list(params.cameras.keys())[:2]:
        logger.info("Starting Cam: {cam}")
        p = Process(target=main, args=(cam,))
        p.start()
        cams.append(p)

    for p in cams:
        p.join()
        
