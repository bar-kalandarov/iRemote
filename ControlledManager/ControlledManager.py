#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import socket
from PIL import ImageGrab
import cStringIO
import pyautogui
from EventMessage.EventMessage import EventMessage
import jsonpickle
import win32api
import win32con
import select
import win32clipboard
import os
import subprocess
import shutil

IMAGE_FORMAT = "jpeg"
LEN_OF_LEN = 10 #Maximum length of message's length
ADDRESS = "0.0.0.0"
PORT = 1600
NUM_TO_LISTEN = 1
TIME_BTW_SCREENSHOT = 1

SCROLL_MOUSE_EVT = "scroll"
LEFT_DOWN_EVT = "left down"
LEFT_UP_EVT = "left up"
RIGHT_DOWN_EVT = "right down"
RIGHT_UP_EVT = "right up"
MOVE_MOUSE_EVT = "move"
MIDDLE_DOWN_EVT = "middle down"
MIDDLE_UP_EVT = "middle up"

MOUSE_EVT_TYPE = 1
KEYBOARD_EVT_TYPE = 2
CLIPBOARD_EVT_TYPE = 3
FILE_EVT_TYPE = 4

ALT = "alt"
TAB = "tab"


class ControlledManager(object):
    def __init__(self):
        self.there_is_a_client = False
        self.is_listen = True
        self.desktop_path = os.path.join(os.path.join(os.environ["USERPROFILE"]), 'Desktop')
        self.command_path = os.getcwd()[:os.getcwd().rfind("\\")] + r"\iRemote\FileHandler\FileHandler\bin\Debug\FileHandler.exe"



    def send_msg(self, control_socket, msg):
        """
        @control_socket: The Socket object of the controller computer.
        @msg: a string to send to the control computer.
        This function send a message to the control computer through comm_handler.
        """
        length = str(len(msg)).zfill(LEN_OF_LEN)
        sent_size = 0
        while sent_size < LEN_OF_LEN:
            rlist, wlist, xlist = select.select([], [control_socket], [], 0.1)
            if wlist is not None:
                size = control_socket.send(length[sent_size:])
                sent_size += size
            else:
                print "wlist is None 1"

        sent_size = 0
        while sent_size < len(msg):
            rlist, wlist, xlist = select.select([], [control_socket], [], 0.1)
            if wlist is not None:
                size = control_socket.send(msg[sent_size:])
                sent_size += size
            else:
                print "wlist is None 2"

    def receive_msg_by_length(self, control_socket, length):
        """
        @control_socket: a Socket object of the controller computer.
        @length: the expected length of the upcoming message.
        This function receives and returns a message, while verify the whole message has been received.
        """
        message = ""
        timeout_in_seconds = 0.1
        try:
            while len(message) < length and self.is_listen:
                ready = select.select([control_socket], [], [], timeout_in_seconds)
                if ready[0]:
                    buf = control_socket.recv(length - len(message))
                    if len(buf) == 0:  # Broken comm_handler!
                            return None
                    message += buf
        except socket.error as msg:
            print "Socket Error: %s" % msg
            return None
        if self.is_listen:
            return message
        return None

    def receive_msg(self, control_socket):
        """
        @control_socket: a Socket object of the controller computer.
        This function receives and returns a message by it's length through a comm_handler.
        """
        length = int(self.receive_msg_by_length(control_socket, LEN_OF_LEN))
        if length is None:
            return None
        msg = self.receive_msg_by_length(control_socket, length)
        if msg is None:
            return None
        return msg

    def stream_screen(self, control_socket):
        """
        @control_socket: a Socket object of the controller computer.
        This function sends screenshot every certain time to the controller.
        """
        while self.there_is_a_client:
            my_file = self.get_screenshot()
            try:
                self.send_msg(control_socket, my_file)
                time.sleep(TIME_BTW_SCREENSHOT)
            except Exception as e:
                print e
                self.there_is_a_client = False

    def receive_events(self, control_socket):
        """
        @control_socket: a Socket object of the controller computer.
        This function receives all kinds of events from the controller and handles each event.
        """
        while self.there_is_a_client:
            try:
                msg = self.receive_msg(control_socket)
                if msg is None:
                    return
                msg = jsonpickle.loads(msg)

                if msg.event_type == MOUSE_EVT_TYPE:
                    self.handle_mouse_events(msg)
                elif msg.event_type == KEYBOARD_EVT_TYPE:
                    self.handle_keyboard_events(msg)
                elif msg.event_type == CLIPBOARD_EVT_TYPE:
                    self.handle_clipboard_events(msg)
                elif msg.event_type == FILE_EVT_TYPE:
                    self.handle_file_events(msg)

            except Exception:
                self.there_is_a_client = False

    def send_screen_size(self, control_socket):
        """
        @control_socket: a Socket object of the controller computer.
        This function sends the details about the screen size of the controlled to the controller.
        """
        self.send_msg(control_socket, str(pyautogui.size()[1]))
        self.send_msg(control_socket, str(pyautogui.size()[0]))

    def handle_file_events(self, event):
        """
        @event: EventMessage object
        This function handles a file event, it creates the received file in the correct directory.
        """
        file_name = event.data[0]
        content = event.data[1]
        x = event.x
        y = event.y
        path = os.getcwd() + r"\TempFiles" + os.sep + str(file_name)
        new_file = open(path, "wb")
        new_file.write(content)
        new_file.close()

        result = subprocess.check_output([self.command_path, str(x), str(y), str(path)])
        if str(result) == "Desktop":
            #os.rename(path, self.desktop_path + os.sep + str(file_name))
            shutil.move(path, self.desktop_path + os.sep + str(file_name))





    @staticmethod
    def handle_clipboard_events(event):
        """
        @event: EventMessage object
        This function handles clipboard events. It changes the current clipboard data to the received data in the event.
        """
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_TEXT, str(event.data))
        win32clipboard.CloseClipboard()


    @staticmethod
    def handle_mouse_events(event):
        """
        @event: EventMessage object
        This function handles mouse events. It simulates mouse events in the Controlled PC according to the received event.
        """
        if event.data == LEFT_DOWN_EVT:
            pyautogui.moveTo(event.x, event.y)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        elif event.data == LEFT_UP_EVT:
            pyautogui.moveTo(event.x, event.y)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        elif event.data == RIGHT_DOWN_EVT:
            pyautogui.moveTo(event.x, event.y)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
        elif event.data == RIGHT_UP_EVT:
            pyautogui.moveTo(event.x, event.y)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
        elif event.data == MIDDLE_DOWN_EVT:
            pyautogui.moveTo(event.x, event.y)
            win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, 0, 0)
        elif event.data == MIDDLE_UP_EVT:
            pyautogui.moveTo(event.x, event.y)
            win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, 0, 0)
        elif event.data == SCROLL_MOUSE_EVT:
            pyautogui.scroll(event.rotation)
        elif event.data == MOVE_MOUSE_EVT:
            pyautogui.moveTo(event.x, event.y)

    @staticmethod
    def handle_keyboard_events(event):
        """
        @event: EventMessage object
        This function handles keyboard events. It simulates mouse presses in the Controlled PC according to the received event.
        """
        if len(event.data) == 3:
            pyautogui.hotkey(event.data[0], event.data[1], event.data[2])
        elif len(event.data) == 2:
            if event.data == [ALT, TAB]:
                pyautogui.keyDown(ALT)
                pyautogui.press(TAB)
            else:
                pyautogui.hotkey(event.data[0], event.data[1])
        else:
            if event.data == [ALT]:
                pyautogui.keyUp(ALT)
            else:
                pyautogui.hotkey(event.data[0])

    @staticmethod
    def get_screenshot():
        """
        This function captures the screen and returns it as a string.
        """
        screenshot = ImageGrab.grab()
        output = cStringIO.StringIO()
        screenshot.save(output, format=IMAGE_FORMAT)
        contents = output.getvalue()
        output.close()
        return contents

    @staticmethod
    def read_file(directory):
        """
        @directory: Where the wanted file is located.
        This function reads and returns the wanted file.
        """
        dst_file = open(directory, "rb")
        dst_file = dst_file.read()
        return dst_file
