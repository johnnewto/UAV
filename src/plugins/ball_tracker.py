""" Example plugin Ball Tracker Plugin
This module contains the implementation of the BallTracker class, which is a plugin for tracking balls in images.
The BallTracker class is a subclass of the plugins Base class and implements the start and on_buffer methods.
"""

import plugins
import cv2
import numpy as np
import socket
import json

class BallTracker(plugins.Base):
    """Class for tracking balls in images."""

    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = ('localhost', 12345)
        self.count = 0

    def start(self, buffer=None):
        """Starts the ball tracker."""
        print("Start Ball Tracker")

    def send_message(self, id, name, pts, offset, rects):
        """Sends a message containing ball information to the server."""
        data = json.dumps({"id": id, "name": name, "pts": pts, "offset": offset, "rects": rects}).encode('utf-8')
        self.client_socket.sendto(data, self.server_address)
        # Wait for ACK, resend if necessary

    def on_buffer(self, id, name, buffer=None):
        """Processes the buffer and detects balls in the image."""
        print("Onbuffer Ball Tracker")
        if buffer is None:
            print("Ball Tracker: buffer is none")
            return
        img = buffer.data
        pts = buffer.pts
        offset = buffer.offset

        gray_img = (cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        a = gray_img.max()
        _, thresh = cv2.threshold(gray_img, a / 2 + 60, a, cv2.THRESH_BINARY)

        kernel = np.ones((6, 6), np.uint8)
        thresh0 = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        contours, hierarchy = cv2.findContours(thresh0, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        rects = []
        for c in contours:
            perimeter = cv2.arcLength(c, True)
            x, y, w, h = cv2.boundingRect(c)
            rects.append([x, y, w, h])
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        image_copy = img.copy()
        final_image = cv2.drawContours(image_copy, contours, contourIdx=-1, color=(0, 255, 0), thickness=2)
        # cv2.imshow('Ball Tracker', final_image)  # this will prob cause problems with the GTK thread
        # cv2.waitKey(1)

        message = f'Ball {self.count = } {rects}'

        print(f'Sending {id}, {name}, {pts}, {offset}, {rects}')
        self.send_message(id, name, pts, offset, rects)
        self.count += 1

