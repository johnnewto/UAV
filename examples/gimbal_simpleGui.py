#!/usr/bin/env python
"""
viewsheen_sdk gimbal control with simplegui
"""
import socket
import time

import cv2

import PySimpleGUI as sg

from GST_Video import GST_Video
# from viewsheen_sdk import GST_Video
from UAV.camera_sdks.viewsheen import gimbal_cntrl

data_received = ''

def socket_function(address, port):
    global data_received
    sock = socket.socket(socket.AF_INET,  # Internet
                         socket.SOCK_DGRAM)  # UDP

    sock.bind((address, port))

    while True:
        data_received = sock.recv(4096, )
        data_received = str(data_received)[2:-1]  # get rid of b/'.....'
        pass

# Class holding the button graphic info. At this time only the state is kept
class BtnInfo:
    def __init__(self, state=True):
        self.state = state        # Can have 3 states - True, False, None (disabled)

def gui():
    sg.theme('LightGreen')

    # define the window layout
    layout = [
      [sg.Text('OpenCV Demo', size=(60, 1), justification='center')],
      # [sg.Image(filename='', key='-IMAGE-')],
      [sg.Button('Toggle', size=(10, 1), k='-TOGGLE1-', border_width=0, button_color='white on green', metadata=BtnInfo())],
      [sg.Button('Forward', size=(10, 1)), sg.Button('Down', size=(10, 1)), sg.Button('Snap', size=(10, 1)), sg.Button('Record', size=(10, 1), button_color='white on green'),],
      [sg.Button('Yaw', size=(10, 1)), sg.Slider((0, 360), 180, 1, orientation='h', size=(40, 15), key='-YAW-', enable_events = True)],
      [sg.Button('Pitch', size=(10, 1)), sg.Slider((-100, 60), 0, 1, orientation='h', size=(40, 15), key='-PITCH-', enable_events=True)],
      [sg.Radio('None', 'Radio', True, size=(10, 1))],
      [sg.Radio('threshold', 'Radio', size=(10, 1), key='-THRESH-'),
       sg.Slider((0, 255), 128, 1, orientation='h', size=(40, 15), key='-THRESH SLIDER-')],
      [sg.Radio('canny', 'Radio', size=(10, 1), key='-CANNY-'),
       sg.Slider((0, 255), 128, 1, orientation='h', size=(20, 15), key='-CANNY SLIDER A-'),
       sg.Slider((0, 255), 128, 1, orientation='h', size=(20, 15), key='-CANNY SLIDER B-')],
      [sg.Radio('blur', 'Radio', size=(10, 1), key='-BLUR-'),
       sg.Slider((1, 11), 1, 1, orientation='h', size=(40, 15), key='-BLUR SLIDER-')],
      [sg.Radio('hue', 'Radio', size=(10, 1), key='-HUE-'),
       sg.Slider((0, 225), 0, 1, orientation='h', size=(40, 15), key='-HUE SLIDER-')],
      [sg.Radio('enhance', 'Radio', size=(10, 1), key='-ENHANCE-'),
       sg.Slider((1, 255), 128, 1, orientation='h', size=(40, 15), key='-ENHANCE SLIDER-')],

      [sg.Text()],
      [sg.Text('           '),sg.RealtimeButton(sg.SYMBOL_UP, key='-GIMBAL-UP-')],
      [sg.RealtimeButton(sg.SYMBOL_LEFT, key='-GIMBAL-LEFT-'), sg.Text(size=(10,1), key='-STATUS-', justification='c', pad=(0,0)),
       sg.RealtimeButton(sg.SYMBOL_RIGHT, key='-GIMBAL-RIGHT-')],
      [sg.Text('           '), sg.RealtimeButton(sg.SYMBOL_DOWN, key='-GIMBAL-DOWN-')],[sg.Text()],
      [sg.Button('Hide', size=(10, 1)), sg.Column([[sg.Button('Exit', size=(10, 1))]], justification='r')],
    ]



    # create the window and show it without the plot
    return sg.Window('OpenCV Integration', layout, location=(800, 400))

def process_frame(frame, values):
    if values['-THRESH-']:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)[:, :, 0]
        frame = cv2.threshold(frame, values['-THRESH SLIDER-'], 255, cv2.THRESH_BINARY)[1]
    elif values['-CANNY-']:
        frame = cv2.Canny(frame, values['-CANNY SLIDER A-'], values['-CANNY SLIDER B-'])
    elif values['-BLUR-']:
        frame = cv2.GaussianBlur(frame, (21, 21), values['-BLUR SLIDER-'])
    elif values['-HUE-']:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        frame[:, :, 0] += int(values['-HUE SLIDER-'])
        frame = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)
    elif values['-ENHANCE-']:
        enh_val = values['-ENHANCE SLIDER-'] / 40
        clahe = cv2.createCLAHE(clipLimit=enh_val, tileGridSize=(8, 8))
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return frame

# Define a function repeat under timer
def timer(window, arg):
   print('win lift')
   window.TKroot.after(1000, timer, arg)

def main(sock=None, timeout=1):
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect to viewsheen_sdk gimbal

    sock.settimeout(timeout)  # Set a timeout
    try:
        sock.connect((gimbal_cntrl.VS_IP_ADDRESS, gimbal_cntrl.VS_PORT))
    except socket.timeout:
        print(f"Timeout connecting to gimbal")
        # return False
    print(f"Connected to gimbal")

    window = gui()
    window.Finalize()

    window.bind('d', '-GIMBAL-RIGHT-')
    window.bind('a', '-GIMBAL-LEFT-')
    window.bind('s', '-GIMBAL-DOWN-')
    window.bind('w', '-GIMBAL-UP-')

    cv2.namedWindow('Receive', cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO | cv2.WINDOW_GUI_EXPANDED)

    video = GST_Video()

    print('Initialising stream...')
    waited = 0
    while not video.frame_available():
        waited += 1
        print('\r  Frame not available (x{})'.format(waited), end='')
        cv2.waitKey(30)

    print('\nSuccess!\nStarting streaming - press "q" to quit.')

    gimbal_speed = 40
    gimbal_key = None
    # event loop
    while True:
        if video.frame_available():
            frame = video.frame().copy()
        else:
            frame = None

        key = cv2.waitKey(1)
        if key != -1:
            window.keep_on_top_clear()

        event, values = window.read(timeout=50)
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event in ('Hide'):
            window.hide()
        if 'TOGGLE' in event:
            window[event].metadata.state = not window[event].metadata.state

        if event in (['Yaw']):
            yaw_val = values['-YAW-']
            print ('Yaw', yaw_val)
            data = gimbal_cntrl.yaw(yaw_val)
            print(data[15:])
            sock.sendall(data)


        if event in (['Pitch']):
            pitch_val = values['-PITCH-']
            print ('Pitch', pitch_val)
            data = gimbal_cntrl.pitch(pitch_val)
            print(data[15:])
            sock.sendall(data)

        if event in (['Forward']):
            key = ord('f')

        if event in (['Down']):
            key = ord('v')
        # if event in ('-UP-', '-LEFT-', '-RIGHT-', '-DOWN-'):
        if 'GIMBAL' in event:
            # if not a timeout event, then it's a button that's being held down
            window['-STATUS-'].update(event)
            if gimbal_key is None:
                if event in ('-GIMBAL-UP-'):
                    gimbal_key = key = ord('w')

                if event in ('-GIMBAL-DOWN-'):
                    gimbal_key = key = ord('s')

                if event in ('-GIMBAL-LEFT-'):
                    gimbal_key = key = ord('a')

                if event in ('-GIMBAL-RIGHT-'):
                    gimbal_key = key = ord('d')

        else:
            # A timeout signals that all buttons have been released so clear the status display
            window['-STATUS-'].update('')
            if gimbal_key is not None:
                gimbal_key = None


        if frame is not None:
            frame = process_frame(frame, values)

            # frame = resize(frame, width=4000)
            # r, c, _ = frame.shape
            # p = (np.array(params.pos)*(r,r,c,c)).astype(int)
            # frame = frame[p[0]:p[1], p[2]:p[3]]

            # print(codes, diffs)
            # print (f"Mean value received = {code0/16:.1f}  {code1/16:.1f} ")
            # cv2.putText(frame, f'Rx: {codes}', (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 15)
            # cv2.imshow('Receive', frame[1900:2200, 1920:2220])

            # shp = frame.shape

            # cv2.putText(frame, f'fps={params.fps}  bitrate={params.bitrate} Kbits/s', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
            # cv2.putText(frame, f'{frame_num:2d} {data_received}', (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
            cv2.imshow('Receive', frame)


        if key == ord('q') or key == ord('Q') or key == 27:
            break

        if key == ord('d'):  # Right arrow key
            print("Right arrow key pressed")
            data = gimbal_cntrl.pan_tilt(gimbal_speed)
            gimbal_cntrl.KeyReleaseThread(sock, data).start()

        if key == ord('a'):  # Left arrow key
            print("Left arrow key pressed")
            data = gimbal_cntrl.pan_tilt(-gimbal_speed)
            gimbal_cntrl.KeyReleaseThread(sock, data).start()

        if key == ord('w'):
            print("Up arrow key pressed")
            data = gimbal_cntrl.pan_tilt(0, gimbal_speed)
            gimbal_cntrl.KeyReleaseThread(sock, data).start()

        if key == ord('s'):
            print("Down arrow key pressed")
            data = gimbal_cntrl.pan_tilt(0, -gimbal_speed)
            gimbal_cntrl.KeyReleaseThread(sock, data).start()

        if key == ord('1'):
            print("Zoom in pressed")
            data = gimbal_cntrl.zoom(1)
            sock.sendall(data)

        if key == ord('2'):
            print("Zoom out pressed")
            data = gimbal_cntrl.zoom(2)
            sock.sendall(data)

        if key == ord('3'):
            print("Zoom stop pressed")
            data = gimbal_cntrl.zoom(2)
            sock.sendall(data)

        if key == ord('4'):
            print("Zoom  = 1")
            data = gimbal_cntrl.zoom(4)
            sock.sendall(data)

        if key == ord('5'):
            print("Zoom x2 in")
            data = gimbal_cntrl.zoom(5)
            sock.sendall(data)

        if key == ord('6'):
            print("Zoom x2 out")
            data = gimbal_cntrl.zoom(6)
            sock.sendall(data)

        if key == ord('c'):
            print("Snapshot pressed")
            data = gimbal_cntrl.snapshot(1, 0)
            gimbal_cntrl.KeyReleaseThread(sock, data).start()

        if key == ord('m'):
            print("Menu pressed")
            window.keep_on_top_set()
            window.un_hide()

        if key == ord('v'):
            print("down pressed")
            data = gimbal_cntrl.oneKeyDown()
            print(data)
            sock.sendall(data)

        if key == ord('f'):
            print("forward pressed")
            data = gimbal_cntrl.forward()
            print(data)
            sock.sendall(data)

        # if key == ord('h'):
        #     print("quickCalibration in pressed")
        #     data = gimbal_cntrl.quickCalibration()
        #     print(data)
        #     sock.sendall(data)

        # if key == ord('t'):
        #     print("trackingStop pressed")
        #     data = gimbal_cntrl.trackingStop()
        #     print(data)
        #     sock.sendall(data)
    # end while
    cv2.destroyAllWindows()
    sock.close()
"""
Test with :
"""

if __name__ == '__main__':

    main()
