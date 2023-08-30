from pymavlink import mavutil
import time
import threading

"""
This is a simple example of a MAVLink camera server.
https://github.com/ArduPilot/pymavlink
https://www.ardusub.com/developers/pymavlink.html
https://mavlink.io/en/



"""
class CameraServer:
    def __init__(self, connection_string, baudrate=57600):
        # Create the connection
        self.master = mavutil.mavlink_connection(connection_string, baud=baudrate)
        self.t = threading.Thread(target=self.send_heartbeat, daemon=True)
        self.t.start()

    def send_heartbeat(self):
        """Send a heartbeat message to indicate the server is alive."""
        while True:
            self.master.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_CAMERA,  # type
                # mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
                mavutil.mavlink.MAV_AUTOPILOT_INVALID,  # autopilot
                0,  # base_mode
                0,  # custom_mode
                mavutil.mavlink.MAV_STATE_ACTIVE,  # system_status
                3  # MAVLink version
            )
            # print("Cam heartbeat_send")
            time.sleep(1)  # Send every second


    def listen(self):
        print("Listening for MAVLink commands...")
        while True:
            # Wait for a MAVLink message
            msg = self.master.recv_match(blocking=True)
            # print (msg)

            # Check if it's a command to control the digital camera
            if msg.get_type() == 'COMMAND_LONG' and msg.command == mavutil.mavlink.MAV_CMD_DO_DIGICAM_CONTROL:
                if msg.param2 == 1:  # check if the trigger capture parameter is set
                    self.trigger_camera(msg.param1)
            elif msg.get_type() == 'COMMAND_LONG' and msg.command == mavutil.mavlink.MAV_CMD_VIDEO_START_STREAMING:
                if msg.param1 >= 1:
                    self.start_streaming(msg.param1)

    def start_streaming(self, camera_id):
        # In a real-world scenario, this would involve starting a video stream.
        # For this example, we'll simply print a message.
        print(f"Camera streaming started on camera {camera_id}")

    def trigger_camera(self,  camera_id):
        # In a real-world scenario, this would involve capturing an image.
        # For this example, we'll simply print a message.
        print(f"Camera triggered! Captured an image on camera {camera_id}")

    def close(self):
        self.master.port.close()
        print("Connection closed")


# if __name__ == "__main__":
#     server = CameraServer("/dev/ttyUSB0")  # Adjust this to your connection string
#     try:
#         server.listen()
#     except KeyboardInterrupt:
#         server.close()
#

if __name__ == "__main__":
    # udpin: Bind to a specific UDP port to listen for incoming messages
    # 14550 is the default port for ArduPilot and PX4, but you can change it as needed
    # it's necessary to receive data from clients (udpout) before starting to send any data
    server = CameraServer("udpin:localhost:14550")
    try:
        server.listen()
    except KeyboardInterrupt:
        server.close()
