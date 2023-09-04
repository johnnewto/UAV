# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/api/20_mavlink.base.ipynb.

# %% auto 0
__all__ = ['UAV_SYSTEM_GCS_CLIENT_ID', 'MAV_TYPE_GCS', 'UAV_SYSTEM_VEHICLE_ID', 'MAV_TYPE_CAMERA', 'LeakyQueue', 'MavLinkBase']

# %% ../../nbs/api/20_mavlink.base.ipynb 7
import time, os, sys

from ..logging import logging

# os.environ['MAVLINK20'] == '1' should be placed in UAV.__init__.py
assert os.environ['MAVLINK20'] == '1', "Set the environment variable before from pymavlink import mavutil  library is imported"

# logging.getLogger("uav").setLevel(logging.DEBUG)
# logging.root.setLevel(logging.INFO)
import threading
import queue
import typing as typ

from pymavlink import mavutil
# from UAV.imports import *   # TODO why is this relative import on nbdev_export?


# %% ../../nbs/api/20_mavlink.base.ipynb 10
class LeakyQueue(queue.Queue):
    """Queue that contains only the last actual items and drops the oldest one."""

    def __init__(
        self,
        maxsize: int = 100,
        on_drop: typ.Optional[typ.Callable[["LeakyQueue", "object"], None]] = None,
    ):
        super().__init__(maxsize=maxsize)
        self._dropped = 0
        self._on_drop = on_drop or (lambda queue, item: None)

    def put(self, item, block=True, timeout=None):
        if self.full():
            dropped_item = self.get_nowait()
            self._dropped += 1
            self._on_drop(self, dropped_item)
        super().put(item, block=block, timeout=timeout)

    @property
    def dropped(self):
        return self._dropped

# %% ../../nbs/api/20_mavlink.base.ipynb 11
UAV_SYSTEM_GCS_CLIENT_ID = 200  # GCS type client (TODO its not clear if this is correct,  255 = GCS)
MAV_TYPE_GCS = mavutil.mavlink.MAV_TYPE_GCS
UAV_SYSTEM_VEHICLE_ID = 1   # 1 = vehicle
MAV_TYPE_CAMERA = mavutil.mavlink.MAV_TYPE_CAMERA

class MavLinkBase:
    """
    Mavlink Camera Base 
    """
    def __init__(self, connection_string, # "udpin:localhost:14550"
                 baudrate=57600, #baud rate of the serial port
                 server_system_ID=UAV_SYSTEM_VEHICLE_ID, # remote or air uav system   1 = vehicle
                 client_system_ID = UAV_SYSTEM_GCS_CLIENT_ID, # GCS system   255 = GCS
                 # mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, # type used in heartbeat
                 # is_server=True, # server or client
                 debug=False, # logging level
                 ):
        self._log = logging.getLogger("uav.{}".format(self.__class__.__name__))
        if debug:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        self._log.setLevel(log_level)
        self.connection_string = connection_string
        self.baudrate = baudrate
        self.server_system_ID = server_system_ID
        self.client_system_ID = client_system_ID

        self.check_message(None)
        self.num_commands_received = 0
        self.num_commands_sent = 0
        self.num_acks_received = 0
        self.message_cnts = {'src_sys':{'MSG_TYPE':'count'}} # message counts, indexed by system and message type


        # self._heartbeat_evt = threading.Event()
        self._heartbeat_que = LeakyQueue(maxsize=10)
        # self._ack_evt = threading.Event()
        self._ack_que = LeakyQueue(maxsize=10)
        

    def server(self, mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, # type used in heartbeat
                    source_system = None, # source system   1 = vehicle, 195 = companion computer
                    target_system = None,  # target system   1 = vehicle, 195 = companion computer
                    source_component = mavutil.mavlink.MAV_COMP_ID_CAMERA, # source component
                    target_component = mavutil.mavlink.MAV_COMP_ID_USER1, # target component
                    do_heartbeat:bool=True, # send heartbeat
                    do_listen:bool=True, # listen for commands
                    do_ack:bool=True): # send ack
        """Set the server defaults."""
        assert not hasattr(self, 'client_server_type'), "server() can only be called once"
        self.client_server_type = "Server"
        self.mav_type = mav_type

        self.source_system = self.server_system_ID if source_system is None else source_system
        self.target_system = self.client_system_ID if target_system is None else target_system
        self.source_component = source_component
        self.target_component = target_component

        self.is_server = True
        self.do_heartbeat = do_heartbeat
        self.do_listen = do_listen
        self.do_ack = do_ack
        self.start_mavlink()
        return self
    
    def client(self, mav_type=mavutil.mavlink.MAV_TYPE_GCS, # type used in heartbeat
                    source_system=None,  # source system   1 = vehicle, 195 = companion computer
                    target_system=None,  # target system   1 = vehicle, 195 = companion computer
                    source_component = mavutil.mavlink.MAV_COMP_ID_USER1, # source component
                    target_component = mavutil.mavlink.MAV_COMP_ID_CAMERA, # target component
                    do_heartbeat:bool=True, # send heartbeat
                    do_listen:bool=True, # listen for commands
                    do_ack:bool=False):  # send ack
        """Set client defaults."""
        assert not hasattr(self, 'client_server_type'), "client() can only be called once"
        self.client_server_type = "Client"
        self.mav_type = mav_type

        self.source_system = self.client_system_ID     if source_system is None else source_system
        self.target_system = self.server_system_ID  if target_system is None else target_system
        self.source_component = source_component
        self.target_component = target_component

        self.is_server = False
        self.do_heartbeat = do_heartbeat
        self.do_listen = do_listen
        self.do_ack = do_ack
        self.start_mavlink()
        return self
        
    
    def start_mavlink(self):
        """Start the MAVLink connection."""
        # Create the connection  Todo add source_system and component options
        self.log.info(f"Starting MAVLink connection... Mavlink version 2 = {mavutil.mavlink20()}")
        # self._ack_evt.clear()
        # self._heartbeat_evt.clear()

        self.master = mavutil.mavlink_connection(self.connection_string, # "udpin:localhost:14550"
                                                 baud=self.baudrate, # baud rate of the serial port
                                                 source_system=int(self.source_system), # source system
                                                 source_component=int(self.source_component), # source component
                                                 mav=2)

        self.master.target_system = self.target_system  # Todo master.target_system gets changed by heart beat
        self.master.target_component = self.target_component
        self.log.info(f"Source system Set: {self.master.source_system}, Source component: {self.master.source_component}")
        self.log.info(f"Target system Set: {self.master.target_system}, Target component: {self.master.target_component}")
        # self.log.info(f"see https://mavlink.io/en/messages/common.html#MAV_COMPONENT")
        time.sleep(0.1)  # Todo delay for connection to establish
        if self.do_heartbeat:
            self._t_heartbeat = threading.Thread(target=self.send_heartbeat, daemon=True)
            self._t_heartbeat.start()
        if self.do_listen:
            self._t_mav_listen = threading.Thread(target=self.listen, daemon=True)
            self._t_mav_listen.start()

        # print(f" {self.client_server_type} Mavlink 2 protocol version: {self.master.mavlink20()}")
        assert self.master.mavlink20(), "Mavlink 2 protocol is not hppening ?, check os.environ['MAVLINK20'] = '1'"
    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return "<{}>".format(self)

    @property
    def log(self) -> logging.Logger:
        return self._log
    
    def send_ping(self):
        """Send a ping message to indicate the server is alive."""
        try:
            self.ping_num += 1
        except:
            self.ping_num = 0
        self.log.info("Sending ping")
        self.master.mav.ping_send(
            int(time.time() * 1000),  # Unix time 
            self.ping_num,  # Ping number
            self.target_system,  # Request ping of this system
            self.target_component,  # Request ping of this component
        )   
    
    def send_heartbeat(self):
        """Send a heartbeat message to indicate the server is alive."""
        self._t_heartbeat_stop = False
        self.log.info(f"Starting heartbeat {self.mav_type} to system: {self.target_system} comp: {self.target_component}")
        while not self._t_heartbeat_stop:
            self.master.mav.heartbeat_send(
                self.mav_type,  # type
                # mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
                mavutil.mavlink.MAV_AUTOPILOT_INVALID,  # autopilot
                0,  # base_mode
                0,  # custom_mode
                mavutil.mavlink.MAV_STATE_ACTIVE,  # system_status
            )
            # print("Cam heartbeat_send")
            time.sleep(1)  # Send every second

    # def _wait_heartbeat(self, mav_type=mavutil.mavlink.MAV_TYPE_CAMERA, timeout:int=3)->bool:
    #     """Wait for a heartbeat, so we know the target system IDs (also it seems to need it to start receiving commands)"""
    #     msg = None
    #     self.log.info(f"Waiting for heartbeat from system: {self.target_system} comp: {self.target_component}")
    #     event_set = self._heartbeat_evt.wait(timeout=timeout)
    #     if event_set:
    #         self.log.debug("Heartbeat received")
    #         self._heartbeat_evt.clear()
    #         return True
    #     else:
    #         self.log.debug("No heartbeat received")
    #         return False

    def wait_heartbeat(self, remote_mav_type=None, # type of remote system
                       timeout:int=1, # seconds
                       tries:int=5)->bool: # number of tries
        """Wait for an heartbeat from target_system and target_component."""
        # Todo is this correct ? Wait for a heartbeat, so we know the target system IDs (also it seems to need it to start receiving commands)
        if remote_mav_type is None:
            self.log.debug(f"Waiting for heartbeat from system: {self.target_system} comp: {self.target_component}")
        else:
            self.log.debug(f"Waiting for heartbeat type: {remote_mav_type} from system: {self.target_system} comp: {self.target_component}")
        count = 0
        while count < tries:
            try:
                msg = self._heartbeat_que.get(timeout=timeout)
                self.log.debug(f"Heartbeat received from src_sys: {msg.get_srcSystem()}, src_comp: {msg.get_srcComponent()} {msg} ")
                # check if the heartbeat is from the correct system and component
                if msg.type == remote_mav_type and msg.get_srcSystem() == self.target_system and msg.get_srcComponent() == self.target_component:
                    return True
                elif msg.get_srcSystem() == self.target_system and msg.get_srcComponent() == self.target_component:
                    return True
            except queue.Empty:  # i.e time out
                count += 1


        self.log.debug(f"No heartbeat received after {tries} tries")
        return False

        
    def wait_ack(self, command_type=None, timeout:int=3, # seconds
                       tries:int=3)->bool: # number of tries
        """Wait for an ack from target_system and target_component."""
        self.log.debug(f"Waiting for ACK for command: {command_type} from system: {self.target_system} comp: {self.target_component}")
        count = 0
        while count < tries:
            try:
                msg = self._ack_que.get(timeout=timeout)
                self.log.debug(f"ACK received from src_sys: {msg.get_srcSystem()}, src_comp: {msg.get_srcComponent()} {msg}")
                if command_type ==  msg.command and msg.get_srcSystem() == self.target_system and msg.get_srcComponent() == self.target_component:
                    self.log.info(f"ACK received from src_sys: {msg.get_srcSystem()}, src_comp: {msg.get_srcComponent()} {msg}")
                    return True
                elif msg.get_srcSystem() == self.target_system and msg.get_srcComponent() == self.target_component:
                    self.log.info(f"ACK received from src_sys: {msg.get_srcSystem()}, src_comp: {msg.get_srcComponent()} {msg}")
                    return True
            except queue.Empty:  # i.e time out
                count += 1
        self.log.debug("No ACK received")
        return False


    def send_command(self, 
                     command_id: int, # mavutil.mavlink.MAV_CMD....
                     params: list,): # list of parameters
        # self.log.debug(f"Sending command: {command_id} to system: {self.target_system} comp: {self.target_component}")

        self.master.mav.command_long_send(
            self.target_system,  # target_system   Todo Tried using self.master.target_system but it didn't work
            self.target_component,  # target_component Todo tried using self.master.target_component but it didn't work
            command_id,  # command id
            0,  # confirmation
            *params  # command parameters
        )
        # self.count_message(msg)
        self.num_commands_sent += 1


    def send_ack(self, msg, ack_result=mavutil.mavlink.MAV_RESULT_ACCEPTED):
        """Send an ACK message to indicate a command was received."""
        # self.log.debug(f"Sending ACK target_system:{self.target_system} target_component:{self.target_component}")
        try:
            self.master.mav.command_ack_send(
                    msg.command,
                    ack_result,  # or other MAV_RESULT enum
                    # todo enabling these causes QGC not to show them
                    int(0),  # progress
                    int(0),  # result_param2
                    self.target_system,  # target_system
                    self.target_component,  # target_component
            )
        except:
            self.master.mav.command_ack_send(
                    msg,
                    ack_result,  # or other MAV_RESULT enum             
            )


    def check_message(self, msg, verbose=False):
        """check message and routing."""
        def lprint(s):
            if verbose:
                # print(s)
                self.log.info(s)

        if msg is None:
            return False

        elif msg.get_type() == "BAD_DATA":
            self.count_message(msg)
            return False

        self.count_message(msg)

        if hasattr(msg, 'target_system'):
            if msg.target_system == 0:
                lprint(f"Rcvd Broadcast message {msg}")
            elif msg.target_system == self.source_system:
                if hasattr(msg, 'target_component'):
                    if msg.target_component == self.source_component or msg.target_component == 0:
                        lprint(f"Rcvd message for self {msg}")
                        return True
                    else:
                        lprint(f"Rcvd message for other component {msg}")
                        return False

                else:
                    lprint(f"Rcvd message no target_component {msg}")
                    return True
            else:
                lprint(f"Rcvd message for other system {msg} ******")
                return False
        else:
            lprint(f"Rcvd message no target_system, {msg}")
            return True

        return False


    def count_message(self, msg):
        """ Count a message by adding it to the message_cnts dictionary. indexed by system and message type"""
        try:
            self.message_cnts[msg.get_srcSystem()][msg.get_type()] += 1
        except Exception as e:
            # print(f"!!!! new Message type {msg.get_type()} from system {msg.get_srcSystem()}")
            sys = msg.get_srcSystem()
            if sys not in self.message_cnts:
                self.message_cnts[sys] = {}
            self.message_cnts[sys][msg.get_type()] = 1

        return True

    def listen(self):
        """Listen for MAVLink commands and trigger the camera when needed."""
        self._t_mav_listen_stop = False
        self.log.info(f"Listening for MAVLink commands from system: {self.target_system}...")
        while not self._t_mav_listen_stop:
            # Wait for a MAVLink message
            try:   # Todo: catch bad file descriptor error
                msg = self.master.recv_match(blocking=True, timeout=1)
            except Exception as e:
                self.log.debug(f"Exception: {e}")
                continue
            if not self.check_message(msg):
                continue
            if msg is None:
                continue

            # self.log.debug(f"Received message {msg}")
            if msg.get_type() == 'COMMAND_LONG':
                self.on_command_rcvd(msg)
                self.num_commands_received += 1
            elif msg.get_type() == 'COMMAND_INT':
                self.on_command_rcvd(msg)
                self.num_commands_received += 1

            elif msg.get_type() == 'COMMAND_ACK':
                # self.log.debug(f"Received ACK ")
                # print(f"**** Received ACK {msg}")
                self.on_ack_rcvd(msg)
                self.num_acks_received += 1
                
            elif msg.get_type() == 'HEARTBEAT':
                # self.log.debug(f"Received HEARTBEAT ")
                self.on_heartbeat_rcvd(msg)
            elif msg.get_type() == 'Ping':
                # self.log.debug(f"Received HEARTBEAT ")
                self.send_ping()
        # finished
        # self.log.info("Stopped")
    
    def on_command_rcvd(self, msg):
        """
        Callback for when a command is received.
        > override this in child class
        """
        # self.log.debug(f"Received message {msg.command}")
        
        if self.do_ack:
            self.send_ack(msg,  mavutil.mavlink.MAV_RESULT_ACCEPTED)

    def on_ack_rcvd(self, msg):
        """
        Callback for when an ack is received.
        > can override this in child class
        """
        # self.log.debug(f"Received ACK {msg.command}")
        # self._ack_evt.set()
        # self._ack_que.put(msg)
        # try:
        self._ack_que.put(msg, block=False)
        # except queue.Full:
        #     print("ACK queue full")
        #     pass
        # pass
    
    def on_heartbeat_rcvd(self, msg):
        """ 
        Callback for when a heartbeat is received.
        > can override this in child class
        """
        # self.log.debug(f"Received HEARTBEAT {msg}")
        # self._heartbeat_evt.set()
        # try:
        self._heartbeat_que.put(msg, block=False)
        # except queue.Full:
        #     print("Heartbeat queue full")
        #     pass
    
 
        
    def _test_command(self, camera_id:int=1): # camera id (0 for all cams)
        """
        Use MAV_CMD_DO_DIGICAM_CONTROL to trigger a camera 
        """
        self.send_command(mavutil.mavlink.MAV_CMD_DO_DIGICAM_CONFIGURE,
                          [camera_id,  # param1 (session)  or cam # (0 for all cams)
                           1,  # param2 (trigger capture)
                           0,  # param3 (zoom pos)
                           0,  # param4 (zoom step)
                           0,  # param5 (focus lock)
                           0,  # param6 (shot ID)
                           0,  # param7 (command ID)
                          ])
        # self.listen_for_ack()
        self.log.info("sent test command MAV_CMD_DO_DIGICAM_CONFIGURE")
        # self.num_commands_sent -= 1   # don't count test command

    def close(self):
        # print(f"Closing {self.__class__.__name__}...")

        self._t_mav_listen_stop = True
        self._t_heartbeat_stop = True
        if self.do_heartbeat:
            self._t_heartbeat.join()
        if self.do_listen:
            self._t_mav_listen.join()

        self.master.close()
        self.master.port.close()
        self.log.info(f"{self.__class__.__name__}  closed")
    
    def __enter__(self):
        """ Context manager entry point for with statement."""
        return self # This value is assigned to the variable after 'as' in the 'with' statement
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point."""
        self.close()
        return False  # re-raise any exceptions
#     


class _Server(MavLinkBase):
    def do_nothing(self):
        pass

class _Client(MavLinkBase):
    def do_nothing(self):
        pass
    
def _test_client_server(debug=False):

# _TEST_HERE = False
# if _TEST_HERE:
    from fastcore.test import test_eq
    # Test sending a command and receiving an ack from client to server
    with _Client("udpin:localhost:14445", server_system_ID=111, client_system_ID=222, debug=debug).client() as client:
        with _Server("udpout:localhost:14445", server_system_ID=111, client_system_ID=222, debug=debug).server() as server:
            client.wait_heartbeat()
            NUM_TO_SEND = 2
            for i in range(NUM_TO_SEND):
                client.send_command(mavutil.mavlink.MAV_CMD_DO_DIGICAM_CONTROL, [0,0,0,0,0,0,0])
                client.wait_ack(timeout=0.1)
                client.send_ping()
                # client.listen_for_ack()
                
            # see if anymore acks come in
            client.wait_ack(timeout=0.1)
    
            print(f"client.num_commands_sent: {client.num_commands_sent}")
            print(f"server.num_commands_received: {server.num_commands_received}")
            print(f"client.num_acks_received: {client.num_acks_received}")

            print(f"server sys: {server.source_system};  msgs: {server.message_cnts}")
            print(f"client sys: {client.source_system};  msgs: {client.message_cnts}")

            test_eq(server.server_system_ID, server.source_system)
            test_eq(client.client_system_ID, client.source_system)
    
            test_eq(client.num_commands_sent, server.num_commands_received)
            test_eq(client.num_acks_received, NUM_TO_SEND)
            test_eq(server.message_cnts[222]['COMMAND_LONG'], client.message_cnts[111]['COMMAND_ACK'])
            assert client.message_cnts[111]['HEARTBEAT'] >= 1

if __name__ == "__main__":
    pass
    _test_client_server(debug=False)
