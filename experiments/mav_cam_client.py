import time
from pymavlink import mavutil

import logging, threading
class CameraClient:
    def __init__(self, connection_string, baudrate=57600):
        # Create the connection
        self._log = logging.getLogger("uav.{}".format(self.__class__.__name__))
        self.master = mavutil.mavlink_connection(connection_string, baud=baudrate)
        # we send a heartnbeat at the start as it seems necessary to send data to server (via udpout) before server will send any data.
        self.send_heartbeat()
        print("Client heartbeat_sent")

        self._t_heartbeat = threading.Thread(target=self.send_heartbeat, daemon=True)
        self._t_heartbeat.start()
        self._t_mav_listen = threading.Thread(target=self.listen, daemon=True)
        self._t_mav_listen.start()

        # Wait for the first heartbeat to get target system and component IDs
        # print("Waiting for heartbeat")
        # first_msg = self.master.recv_match(type='HEARTBEAT', blocking=True)
        # print("Heartbeat from system (system %u component %u)" % (self.master.target_system, self.master.target_component))
        # self.master.wait_heartbeat()
        # print("Connected to MAVLink device")

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return "<{}>".format(self)

    @property
    def log(self) -> logging.Logger:
        return self._log


    def wait_for_heartbeat(self):
        # Wait for the first heartbeat to get target system and component IDs
        self.log.info("Waiting for heartbeat")
        first_msg = self.master.recv_match(type='HEARTBEAT', blocking=True)
        self.log.info("Heartbeat from system (system %u component %u)" % (self.master.target_system, self.master.target_component))
        self.master.wait_heartbeat()
        self.log.info("Connected to MAVLink device")
    def trigger_camera(self, camera_id=1):
        # Use MAV_CMD_DO_DIGICAM_CONTROL to trigger the camera
        # This assumes the camera understands this MAVLink message
        self.master.mav.command_long_send(
            self.master.target_system,  # target_system
            self.master.target_component,  # target_component
            mavutil.mavlink.MAV_CMD_DO_DIGICAM_CONTROL,  # command
            0,  # confirmation
            camera_id,  # param1 (session)  or cam # (0 for all cams)
            1,  # param2 (trigger capture)
            0,  # param3 (zoom pos)
            0,  # param4 (zoom step)
            0,  # param5 (focus lock)
            0,  # param6 (shot ID)
            0,  # param7 (command ID)
        )
        print("sent Camera trigger")

    def start_streaming(self, camera_id=1):
        # Use MAV_CMD_VIDEO_START_STREAMING to start streaming video
        # This assumes the camera understands this MAVLink message
        self.master.mav.command_long_send(
            self.master.target_system,  # target_system
            self.master.target_component,  # target_component
            mavutil.mavlink.MAV_CMD_VIDEO_START_STREAMING,  # command
            0,  # confirmation
            camera_id,  # param1 (camera ID) Video Stream ID (0 for all streams, 1 for first, 2 for second, etc.)
            0,  # param2 (frame rate in Hz)
            0,  # param3 (0=disabled, 1=enabled)
            0,  # param4
            0,  # param5
            0,  # param6
            0,  # param7
        )
        print("sent Start streaming")

    def stop_streaming(self, camera_id=1):
        # Use MAV_CMD_VIDEO_STOP_STREAMING to stop streaming video
        # This assumes the camera understands this MAVLink message
        self.master.mav.command_long_send(
            self.master.target_system,  # target_system
            self.master.target_component,  # target_component
            mavutil.mavlink.MAV_CMD_VIDEO_STOP_STREAMING,  # command
            0,  # confirmation
            camera_id,  # param1 (camera ID) Video Stream ID (0 for all streams, 1 for first, 2 for second, etc.)
            0,  # param2
            0,  # param3
            0,  # param4
            0,  # param5
            0,  # param6
            0,  # param7
        )
        print("sent Stop streaming")

    def video_stream_info(self, camera_id=1):
        # Use MAV_CMD_REQUEST_MESSAGE to request video stream info
        # This assumes the camera understands this MAVLink message
        self.master.mav.command_long_send(
            self.master.target_system,  # target_system
            self.master.target_component,  # target_component
            mavutil.mavlink.MAV_CMD_REQUEST_VIDEO_STREAM_INFORMATION,  # command
            0,  # confirmation
            camera_id,  # param1 (camera ID) Video Stream ID (0 for all streams, 1 for first, 2 for second, etc.)
            0,  # param2 Video Stream ID (1 for first, 2 for second, etc.)
            0,  # param3
            0,  # param4
            0,  # param5
            0,  # param6
            0,  # param7
        )
        self.log.info("sent Request stream info")


    def send_heartbeat(self):
        self.master.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GCS,  # type
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,  # autopilot
            0,  # base_mode
            0,  # custom_mode
            mavutil.mavlink.MAV_STATE_ACTIVE,  # system_status
            3  # MAVLink version
        )

    def listen(self):
        print("Listening for MAVLink ...")


        while True:
            # Wait for a MAVLink message
            msg = self.master.recv_msg()
            if msg:
                self.log.info(msg)
            else:
                # print("No message")
                time.sleep(0.1)

    def close(self):
        self.master.port.close()
        self.log.info("Connection closed")


# if __name__ == "__main__":
#     client = CameraClient("udp:127.0.0.1:14550")  # Adjust this to your connection string
#     time.sleep(2)  # Give it a little time after connecting before triggering the camera
#     client.trigger_camera()
#     client.close()
#
#
if __name__ == "__main__":
    # udpout: Outputs data to a specified address:port (client).
    # it's necessary to send data to server (udpout) before server will send any data.
    client = CameraClient("udpout:localhost:14550")
    # time.sleep(0.1)
    # client.trigger_camera()
    client.video_stream_info(1)
    time.sleep(1)
    while True:
        client.trigger_camera(1)
        time.sleep(1)
        client.start_streaming(1)
        time.sleep(1)
        client.trigger_camera(2)
        time.sleep(1)
        client.start_streaming(2)
        time.sleep(1)
        client.trigger_camera(3)
        time.sleep(1)
        client.start_streaming(3)
        time.sleep(1)

    client.close()
    #
    # try:
    #     client.listen()
    # except KeyboardInterrupt:
    #     client.close()
