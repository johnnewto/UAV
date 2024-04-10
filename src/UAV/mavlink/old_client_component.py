from __future__ import annotations

__all__ = ['NAN', 'ClientComponent', 'Component']

import asyncio
import contextlib

from .component import Component, mavlink, mavutil
from ..logging import LogLevels

NAN = float("nan")


def patch_MAVLink_camera_information_message():
    """Override/patch format_attr to handle vender and model name list as a string rather than list of ints.
    See ardupilotmega.py line 143
    `def format_attr(self, field: str) -> Union[str, float, int]:`
    """
    # print("patch_MAVLink_camera_information_message.format_attr;   to handle vender and model name list")
    from typing import List, Union
    import sys
    def format_attr(msg, field: str) -> Union[str, float, int, bytes]:
        """override field getter"""
        raw_attr: Union[bytes, float, int] = getattr(msg, field)
        if isinstance(raw_attr, bytes):
            if sys.version_info[0] == 2:
                return raw_attr.rstrip(b"\x00")
            return raw_attr.decode(errors="backslashreplace").rstrip("\x00")
        elif isinstance(raw_attr, List):
            return str(''.join(chr(i) for i in raw_attr)).rstrip()
        return raw_attr

    mavlink.MAVLink_camera_information_message.format_attr = format_attr


patch_MAVLink_camera_information_message()


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


class ClientComponent(Component):
    """Create a client component to send commands to a companion computer or GCS that will control a cameras via a CameraServer instance """

    def __init__(self,
                 source_component: int,  # used for component indication
                 mav_type: int,  # used for heartbeat MAV_TYPE indication
                 loglevel: LogLevels | int = LogLevels.INFO,  # logging level
                 ):

        super().__init__(source_component=source_component, mav_type=mav_type, loglevel=loglevel)

        self.append_message_callback(self.on_message)
        self._message_callback_conds = []

    def set_message_callback_cond(self, msg_id, target_system, target_component):
        """Register a callback condition for a message received from a component server"""
        evt = asyncio.Event()
        cond = {'msg_id': msg_id, 'target_system': target_system, 'target_component': target_component, 'event': evt,
                'msg': None}
        self._message_callback_conds.append(cond)
        self.log.debug(f"{len( self._message_callback_conds) = } ")
        return cond

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

    async def message_callback_cond(self, msg_id, target_system, target_component, timeout=1):
        """Register a callback for a message received from a component server
           Returns the message """
        evt = asyncio.Event()
        cond = {'msg_id': msg_id, 'target_system': target_system, 'target_component': target_component, 'event': evt,
                'msg': None}
        self._message_callback_conds.append(cond)
        self.log.debug(f"{len( self._message_callback_conds) = } ")
        # await asyncio.sleep(0.1)
        ret = await event_wait(evt, timeout)
        try:
            self._message_callback_conds.remove(cond)
        except ValueError:
            self.log.error(
                f"Failed to remove callback condition {msg_id = } {target_system = } {target_component = } {timeout = } {evt = }")
        return cond['msg']

    def on_mav_connection(self):
        super().on_mav_connection()

    def on_message(self, msg: mavlink.MAVLink_message):
        """Callback for a command received from a component server """
        # self.log.debug(f"Rcvd {msg.get_srcSystem()}/{msg.get_srcComponent()} {msg} ")
        for cond in self._message_callback_conds:
            if msg.get_msgId() == cond['msg_id'] and msg.get_srcSystem() == cond[
                'target_system'] and msg.get_srcComponent() == cond['target_component']:
                # self.log.debug(f"RCVD: {msg.get_srcSystem()}/{msg.get_srcComponent()}: CAMERA_Client  {msg} ")
                cond['event'].set()
                cond['msg'] = msg  # add the message to the condition, so it can be returned

    def send_message(self, msg):
        """Send a message to a component server"""
        self.master.mav.send(msg)
        self.log.debug(f"Sent {msg}")

    # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_MESSAGE
    async def request_message(self, msg_id, params=None, target_system=None, target_component=None, timeout=1):
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

    async def request_message_stream(self, target_system=None, target_component=None,
                                     msg_id: int = mavutil.mavlink.MAVLINK_MSG_ID_BATTERY_STATUS,  # https://mavlink.io/en/messages/common.html
                                     interval: int = 1000000,  # interval in microseconds
                                     response_target:int = 0): # 0: Flight-stack default (recommended), 1: address of requestor, 2: broadcast. See https://mavlink.io/en/messages/common.html#MAV_CMD_SET_MESSAGE_INTERVAL
        """ A system can request that additional messages are sent as a stream, or change the rate at which existing streamed messages are sent,
        using the MAV_CMD_SET_MESSAGE_INTERVAL command. A single instance of a message can be requested by sending MAV_CMD_REQUEST_MESSAGE.
        See https://mavlink.io/en/mavgen_python/howto_requestmessages.html
        See https://mavlink.io/en/messages/common.html#MAV_CMD_SET_MESSAGE_INTERVAL"""

        tgt_sys, tgt_comp  = check_target(self, target_system, target_component)
        cond = self.set_message_callback_cond(msg_id, tgt_sys, tgt_comp)
        await self.send_command(tgt_sys, tgt_comp,
                              mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_MESSAGE_INTERVAL
                              [
                               msg_id,  # https://mavlink.io/en/messages/common.html
                               interval, 0, 0, 0, 0, 0]
                              )
        await self.wait_message_callback(cond)
        return cond['msg']