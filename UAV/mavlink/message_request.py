from __future__ import annotations

__all__ = ['NAN', 'CAMERA_INFORMATION', 'CAMERA_SETTINGS', 'STORAGE_INFORMATION', 'CAMERA_CAPTURE_STATUS',
           'CAMERA_IMAGE_CAPTURED', 'CameraServer', 'Component']

import asyncio
import contextlib
import queue

import pymavlink.dialects.v20.ardupilotmega as mavlink
from pymavlink import mavutil
from pymavlink.dialects.v20.ardupilotmega import MAVLink

# from .mavcom import MAVCom, time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
# from .component import Component
from ..logging import logging, LogLevels
from ..utils.general import LeakyQueue, get_linenumber


# logging.getLogger("uav").setLevel(logging.DEBUG)
# logging.root.setLevel(logging.INFO)
def mavlink_command_to_string(command_id):
    try:
        return mavutil.mavlink.enums['MAV_CMD'][command_id].name
    except:
        return command_id


def check_target(obj, target_system, target_component):
    """Check if the target_system and target_component are set and return them"""
    target_system = obj.target_system if target_system is None else target_system
    target_component = obj.target_component if target_component is None else target_component
    assert target_system is not None and target_component is not None, "call set_target(target_system, target_component) first"
    return target_system, target_component


async def event_wait(evt, timeout):
    # suppress TimeoutError because we'll return False in case of timeout
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(evt.wait(), timeout)
    return evt.is_set()


class MessageRequest:
    """Create a mavlink Camera server Component, cameras argument will normally be a  gstreamer pipeline"""

    def __init__(self,
                 mav_com,
                 # source_component=mavlink.MAV_COMP_ID_CAMERA,  # used for component indication
                 # mav_type=mavlink.MAV_TYPE_CAMERA,  # used for heartbeat MAV_TYPE indication
                 # camera=None,  # cameras  (or FakeCamera for testing)
                 loglevel: LogLevels | int = LogLevels.INFO,  # logging level
                 ):

        # super().__init__(source_component=source_component, mav_type=mav_type, loglevel=loglevel)

        self._log = None
        self._ack_que = LeakyQueue(maxsize=10)
        self._message_callback_conds = []
        self.source_system = None
        # self.source_component = source_component
        self.set_log(loglevel)
        self._loop = asyncio.get_event_loop()

        self.ping_num = 0
        self.max_pings = 4
        self.num_msgs_rcvd = 0
        self.num_cmds_sent = 0
        self.num_cmds_rcvd = 0
        self.num_acks_sent = 0
        self.num_acks_rcvd = 0
        self.num_acks_drop = 0
        self.mav_com = mav_com
        self.master = mav_com.master

        # self.task = asyncio.create_task(self.run_rc_poll())

        # self.log.info(f"CameraServer created {self.camera = }")

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return "<{}>".format(self)

    def set_log(self, loglevel):
        self._log = logging.getLogger("uav.{}".format(self.__class__.__name__))
        self._log.setLevel(int(loglevel))

    @property
    def log(self) -> logging.Logger:
        return self._log

    def set_mav_connection(self, mav_com: "MAVCom"):

        # def start_mav_connection(self, mav_connection: "MAVCom"):
        """Set the mav_connection for the component"""
        self.mav_com = mav_com
        self.master = mav_com.master
        self.mav: MAVLink = mav_com.master.mav
        self.source_system = mav_com.source_system
        self.log.debug(f"set_mav_connection {self.__class__.__name__} {get_linenumber()} {self.mav_com = }")
        # self._t_heartbeat.start()
        self._t_command.start()
        self.on_mav_connection()
        self.log.info(
            f"Component Started {self.source_component = }, {self.mav_type = }, {self.source_system = }")

    def on_mav_connection(self):
        self.log.debug("Called from Component.start_mav_connection(), override to add startup behaviour")

    async def wait_message_callback(self, cond, timeout=1, remove_after=True):
        """Wait for the callback for a message received from a component server"""
        ret = await event_wait(cond['event'], timeout)
        if remove_after:
            try:
                self._message_callback_conds.remove(cond)
            except ValueError:
                self.log.warning(f"Failed to remove callback condition {cond}")
                self.log.warning(f"message_callback_conds{self._message_callback_conds}")
        return ret

    def set_message_callback_cond(self, msg_id, target_system, target_component):
        """Register a callback condition for a message received from a component server"""
        evt = asyncio.Event()
        cond = {'msg_id': msg_id, 'target_system': target_system, 'target_component': target_component, 'event': evt,
                'msg': None}
        self._message_callback_conds.append(cond)
        self.log.debug(f"{len( self._message_callback_conds) = } ")
        return cond

    def set_source_compenent(self):
        """Set the source component for the master.mav """
        if self.master is None:
            print(f"{self.__class__.__name__} {get_linenumber()} {self.master = }")
        assert self.master is not None, "self.master is None"
        self.master.mav.srcComponent = self.source_component

    async def request_message(self, msg_id, params=None, target_system=None, target_component=None, timeout=2):
        """ Request the target system(s) emit a single instance of a specified message (i.e. a "one-shot" version of MAV_CMD_SET_MESSAGE_INTERVAL).
        https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_MESSAGE"""
        if params is None:
            params = [0, 0, 0, 0, 0, 0]
        tgt_sys, tgt_comp = check_target(self, target_system, target_component)

        cond = self.set_message_callback_cond(msg_id, tgt_sys, tgt_comp)
        await self.send_command(tgt_sys, tgt_comp,
                                mavlink.MAV_CMD_REQUEST_MESSAGE,  # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_MESSAGE
                                [msg_id] + params
                                )

        await self.wait_message_callback(cond, timeout=timeout)
        return cond['msg']

    async def run_rc_poll(self):
        """Run a thread to poll the RC channels"""
        # self.rc_thread = threading.Thread(target=self.rc_poll, daemon=True)
        # self.rc_thread.start()
        while True:
            msg = await self.request_message(msg_id=mavlink.MAVLINK_MSG_ID_RC_CHANNELS, target_system=1, target_component=1, timeout=1)
            self.log.info(f"request_message {msg}")
            # print(f"request_message {msg}")
            if msg == mavlink.MAVLINK_MSG_ID_RC_CHANNELS:
                print(f"request_message {msg}")
                if msg.chancount == 0:
                    print("RC might not be connected")
            if msg is not None:
                # RC channel 7 switch is used to trigger the message
                print(f"{msg.chan7_raw = }  ", end='')
                print(
                    f"RC_CHANNELS: chancount = {msg.chancount}: {msg.chan1_raw}, {msg.chan2_raw}, {msg.chan3_raw}, {msg.chan4_raw}, {msg.chan5_raw}, {msg.chan6_raw}, {msg.chan7_raw}, {msg.chan8_raw}, {msg.chan9_raw}, {msg.chan10_raw}, {msg.chan11_raw}, {msg.chan12_raw}, {msg.chan13_raw}, {msg.chan14_raw}, {msg.chan15_raw}, {msg.chan16_raw}, {msg.chan17_raw}, {msg.chan18_raw}")

    async def send_command(self, target_system: int,  # target system
                           target_component: int,  # target component
                           command_id: int,  # mavutil.mavlink.MAV_CMD....
                           params: list,  # list of parameters
                           timeout=0.5,  # seconds
                           ):
        self.log.debug(
            f"Sending: {target_system}/{target_component} : {mavlink_command_to_string(command_id)}:{command_id} ")
        self.set_source_compenent()
        self.master.mav.command_long_send(
            target_system,  # target_system   Todo Tried using self.master.target_system but it didn't work
            target_component,  # target_component Todo tried using self.master.target_component but it didn't work
            command_id,  # command id
            0,  # confirmation
            *params  # command parameters
        )
        self.num_cmds_sent += 1

        ret = await self.wait_ack(target_system, target_component, command_id=command_id, timeout=timeout)
        if ret:
            # if self.wait_ack(target_system, target_component, command_id=command_id, timeout=timeout):
            self.log.debug(
                f"Rcvd ACK: {target_system}/{target_component} {mavlink_command_to_string(command_id)}:{command_id}")
            self.num_acks_rcvd += 1
            return True
        else:
            self.log.warning(
                f"**No ACK: {target_system}/{target_component} {mavlink_command_to_string(command_id)}:{command_id}")
            self.num_acks_drop += 1
            return False

    async def wait_ack(self, target_system, target_component, command_id=None, timeout=0.1) -> bool:
        """Wait for an ack from target_system and target_component."""
        self.log.debug(
            f"Waiting for ACK: {target_system}/{target_component} : {mavlink_command_to_string(command_id)}:{command_id}")
        _time = 0
        _TIME_STEP = 0.1
        while _time < timeout:
            _time += _TIME_STEP
            # print(f"{_time = }")
            try:
                msg = self._ack_que.get_nowait()
                # msg = self._ack_que.get(timeout=_TIME_STEP)
                # self.log.debug(f"ACK received from src_sys: {msg.get_srcSystem()}, src_comp: {msg.get_srcComponent()} {msg}")
                if (
                        command_id == msg.command or command_id is None) and msg.get_srcSystem() == target_system and msg.get_srcComponent() == target_component:
                    self.log.debug(
                        f"Rcvd ACK: {msg.get_srcSystem()}/{msg.get_srcComponent()} {mavlink_command_to_string(msg.command)}:{msg.command} {msg.get_srcComponent()} {msg}")
                    return True
                else:
                    self.log.warning(
                        f"**** ACK not handled {mavlink_command_to_string(msg.command)}:{msg.command} from : {msg.get_srcSystem()}/{msg.get_srcComponent()} {msg}")
                    # print(f"{command_id = } {msg.get_srcSystem() = }, {target_system = },  {msg.get_srcComponent() = }, {target_component = }")
                    self.log.warning(
                        f"      command_id = {mavlink_command_to_string(msg.command)} {msg.get_srcSystem() = }, {target_system = },  {msg.get_srcComponent() = }, {target_component = }")

            except queue.Empty:  # i.e time out
                await asyncio.sleep(_TIME_STEP)
                pass

        self.log.debug("!!!!*** No ACK received")
        return False

    def close(self):
        """Close """
        pass
        # if self.camera is not None:
        #     self.camera.close()
        # super().close()
        # self.log.debug(f"Closed connection to cameras")
        # return True
