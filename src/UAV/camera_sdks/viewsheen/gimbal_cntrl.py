

import socket
import cv2, time
import numpy as np
import threading
try:
    from pynput import keyboard, mouse
except ImportError:
    print("pynput not installed, install with pip install pynput")

# Define the IP address and port number of the viewsheen_sdk gimbal
VS_IP_ADDRESS = '192.168.144.200'
VS_PORT = 2000
# IP_ADDRESS = "10.5.0.2"  # send to drone from the GS
# PORT = 2000

wCRC_Table = [
    0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
    0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400
]
def crc_fly16(pBuffer, length):
    crcTmp = 0xFFFF
    for i in range(length):
        tmp = wCRC_Table[(pBuffer[i] ^ crcTmp) & 15] ^ (crcTmp >> 4)
        crcTmp = wCRC_Table[((pBuffer[i] >> 4) ^ tmp) & 15] ^ (tmp >> 4)
    return crcTmp


def int16_to_bytes(value):
    # Extract the low and high bytes
    low_byte = value & 0xFF
    high_byte = (value >> 8) & 0xFF
    # Return the bytes as a bytearray
    return bytearray([low_byte, high_byte])

def pan_tilt(pan=0.0, tilt=0.0):
    ''' pan and or tilt in deg / sec with max of 100 deg / sec'''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x04
    lower_bound , upper_bound = -10000, 10000
    pan = max(lower_bound, min(int(pan * 100), upper_bound))
    tilt = max(lower_bound, min(int(tilt * 100), upper_bound))
    D1_6 = np.array([pan, tilt, 0], dtype=np.int16).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def zoom(Byte1):
    ''' zoom
        Byte1=1：Zoom in
        Byte1=2：Zoom out
        Byte1=3：Stop
        Byte1=4：ZOOM=1
        Byte1=5：2× Zoom in
        Byte1=6：2× Zoom out
    '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x12
    lower_bound, upper_bound = 1, 6
    d1 = max(lower_bound, min(int(Byte1), upper_bound))
    D1_6 = np.array([d1, 0, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum


def snapshot(Byte1, Byte2):
    ''' snapshot
        Byte1：
            0x01: single shot
            0x02: continuous shooting
            0x03: time-lapse shooting
            0x04: timed shot
            0x05: Stop shooting.
        Byte2：
            If Byte1= 0x02, Byte2= Number of continuous shots
            If Byte1= 0x03, Byte2= Delayed time (Sec)
            If Byte1= 0x04, Byte2= Timed time (Sec)
        '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x10
    lower_bound, upper_bound = 1, 5
    D1 = max(lower_bound, min(int(Byte1), upper_bound))
    lower_bound, upper_bound = 0, 255
    D2 = max(lower_bound, min(int(Byte2), upper_bound))
    D1_6 = np.array([D1, D2, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def yaw(angle):
    ''' yaw
        Byte1=1：
        Byte2-3: Angle of Yaw*10[0,3600] 2 Low 3 High
        '''
    # return # todo this is not working JN
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x08
    lower_bound, upper_bound = 0, 3600
    angle = max(lower_bound, min(int(angle*10), upper_bound))
    [low_byte, high_byte] = int16_to_bytes(angle)
    D1_6 = np.array([1, low_byte, high_byte, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def pitch(angle):
    ''' pitch
        Byte1=2：
        Byte2-3: Angle of Pitch *10[-1000,600]  2 Low 3 High；
    '''

    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x08
    lower_bound, upper_bound = -1000, 600
    angle = max(lower_bound, min(int(angle*10), upper_bound))
    [low_byte, high_byte] = int16_to_bytes(angle)
    D1_6 = np.array([2, low_byte, high_byte, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def oneKeyDown():
    ''' point down
        '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x07
    D1_6 = np.array([0, 0, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def forward():
    ''' point down
        '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x02
    D1_6 = np.array([0, 0, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum

def quickCalibration():
    ''' point down
    0xF0: Quick Calibration
        '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0xF0
    D1_6 = np.array([0, 0, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum


def trackingStop():
    ''' Tracking stop
        '''
    HEADER = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88".replace(" ", "")
    S_ID = 0x0f
    COMMAND = 0x06
    D1_6 = np.array([0, 0, 0, 0, 0, 0], dtype=np.int8).tobytes()
    data = bytes.fromhex(HEADER)+bytearray([S_ID, COMMAND]) + D1_6
    checksum = int16_to_bytes(crc_fly16(data, len(data)))
    return data+checksum


# KeyReleaseThreadExists = None
_lock_KRT = threading.Lock()
class KeyReleaseThread(threading.Thread):
    def __init__(self, sock=None, data=None):
        # if threadExists == False:
        #     print( 'KeyReleaseThread already running')
        # else:
        #     KeyReleaseThreadExists = True
        super().__init__()
        self.sock = sock
        self.data = data
        self.release_event = threading.Event()
        self.listener = None
        self._running = False

    def run(self):
        if _lock_KRT.locked():
            print("KeyReleaseThread locked")
            return
        _lock_KRT.acquire()
        # with lock:
        print("Starting KeyReleaseThread")
        self._running = True
        def on_key_release(key):
            print('on_key_release', key)
            self.release_event.set()

        def on_click(x, y, button, pressed):
            print('on_click', x, y, button, pressed)
            self.release_event.set()

        self.key_listener = keyboard.Listener(on_release=on_key_release)
        self.key_listener.start()
        self.mouse_listener = mouse.Listener(on_click=on_click)
        self.mouse_listener.start()
        while self._running:

            self.release_event.wait(0.05)  # Wait 50 msecs
            if self.release_event.is_set():
                self._running = False
                break
            else:
                if self.sock is not None:
                    self.sock.sendall(self.data)
                # print('Wait 50 msecs')

        self.key_listener.stop()
        self.mouse_listener.stop()
        self._running = False
        _lock_KRT.release()
        print("Stopped KeyReleaseThread ..")
        # time.sleep(0.5)

    def stop(self):
        self._running = False

# def TryMoveGimbal(sock, data):
#     def __init__(self, sock=None, data=None):
#
#     KeyReleaseThread(sock, data).start()
#
#     if
# right = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88 0f 04 40 1f 00 00 00 00 c0 5c".replace(" ", "")
# # right = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88 0f 04 40 1f 00 00 00 00 00 00".replace(" ", "")
# left = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88 0f 04 c0 e0 00 00 00 00 cb 88".replace(" ", "")
# up = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88 0f 04 00 00 40 1f 00 00 7f 58".replace(" ", "")
# down = "eb 90 0a 00 00 00 00 00 00 00 00 00 40 88 0f 04 00 00 c0 e0 00 00 66 a8".replace(" ", "")
#
# data = bytes.fromhex(right)  # Convert the hex data to bytes
# print(data)

if __name__ == "__main__":
    # Create a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)   # Set the socket timeout to 2 seconds
    # Connect to viewsheen_sdk gimbal
    sock.connect((VS_IP_ADDRESS, VS_PORT))

    cv2.imshow('RTSP Stream', np.zeros((100,100,3), 'uint8'))
    gimbal_speed = 20
    keyThread = KeyReleaseThread(sock)

    while True:
        key = cv2.waitKey(10)
        if key != -1:
            print (key)
        if key == ord('q') or key == 27:
            break

        if key == ord('d'):  # Right arrow key
            print("Right arrow key pressed")
            data = pan_tilt(gimbal_speed)
            KeyReleaseThread(sock, data).start()


        if key == ord('a'):  # Left arrow key
            print("Left arrow key pressed")
            data = pan_tilt(-gimbal_speed)
            KeyReleaseThread(sock, data).start()

        if key == ord('w'):
            print("Up arrow key pressed")
            data = pan_tilt(0, gimbal_speed)
            KeyReleaseThread(sock, data).start()

        if key == ord('s'):
            print("Down arrow key pressed")
            data = pan_tilt(0, -gimbal_speed)
            KeyReleaseThread(sock, data).start()

        if key == ord('z'):
            print("Zoom in pressed")
            data = zoom(0)
            KeyReleaseThread(sock, data).start()

        if key == ord('c'):
            print("Snapshot in pressed")
            data = snapshot(1,0)
            sock.sendall(data)

        if key == ord('p'):
            print("pitch in pressed")
            data = pitch(45)
            print(data)
            sock.sendall(data)

        if key == ord('y'):
            print("yaw in pressed")
            data = yaw(45)
            print(data)
            sock.sendall(data)
            KeyReleaseThread(sock, data).start()

        if key == ord('v'):
            print("down in pressed")
            data = oneKeyDown()
            print(data)
            sock.sendall(data)

        if key == ord('f'):
            print("forward  pressed")
            data = forward()
            print(data)
            sock.sendall(data)

    # Close the socket
    sock.close()
    cv2.destroyAllWindows()