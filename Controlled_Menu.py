# -*- coding: utf-8 -*-
import socket
import threading
import select
import random
import hashlib
import os
import re

import wx

from ControlledManager.ControlledManager import ControlledManager


ADDRESS = "0.0.0.0"
PORT = 1700
NUM_TO_LISTEN = 5
CONTROLLED_MENU_TITLE = "Controlled Menu"

UNDER_CONTROL_MSG = "Already Controlled"
VALID_CODE_MSG = "Correct Code"
INVALID_CODE_MSG = "Incorrect Code"
SELECT_TIMEOUT = 0.1
CONTROLLED_FRAME_SIZE = (800, 480)
SECOND_IN_MINUTE = 60
CODE_CHANGE_DURATION = 2 # Minutes
RANDOM_NUM_RANGE = 100000
LEN_OF_CODE = 5
BACKGROUND_PATH = r"Images\Background2.png"
IP_LABEL_POS = (330, 112)
IP_LABEL_SIZE = (100, 20)
CODE_LABEL_SIZE = (100, 20)
CODE_LABEL_POS = (330, 190)

class ControlledApp(wx.App):
    def __init__(self):
        super(ControlledApp, self).__init__()
        self.server_manager = None
        self.frame = ControlledFrame(None, title=CONTROLLED_MENU_TITLE)


    def OnExit(self):
        """
        This function overrides the OnExit function of wx.App.
        It is called when the user exits the application.
        """
        self.clean_threads()

    def clean_threads(self):
        """
        This function closes all the open threads.
        """
        self.server_manager.com_handler.is_listen = False
        if self.server_manager is not None:
            self.server_manager.com_handler.there_is_a_client = False

            if self.server_manager.stream_thread is not None:
                self.server_manager.stream_thread.join()

            if self.server_manager.events_thread is not None:
                self.server_manager.events_thread.join()

            self.server_manager.on_air = False
            self.server_manager.join()
            self.server_manager.server_socket.close()
            self.server_manager.server_socket = None


class ServerThread(threading.Thread):
    """Simple thread that sends an update to its
    target window once a second with the new count value.
    """
    def __init__(self, targetwin):
        super(ServerThread, self).__init__()
        self.open_clients_sockets = []
        self.messages_to_send = []
        self.controller_socket = None
        self.com_handler = ControlledManager()
        self.server_socket = socket.socket()
        # Attributes
        self.targetwin = targetwin
        self.there_is_connection = False
        self.on_air = False

        self.events_thread = None
        self.stream_thread = None

    def send_waiting_messages(self):
        """
        The function handles all the waiting messages in the self.messages_to_send list.
        The function sends each message to its destination.
        """
        for message in self.messages_to_send:
            (client_socket, data) = message
            self.com_handler.send_msg(client_socket, data)
            self.messages_to_send.remove(message)
            if client_socket is self.controller_socket:
                self.start_connection()

    def run(self):
        """
        This function starts the thread process: Accepting new client, handles the connection process.
        """
        if self.targetwin:
            self.on_air = True
            self.server_socket.bind((ADDRESS, PORT))
            self.server_socket.listen(NUM_TO_LISTEN)

            while self.on_air:
                if not self.check_if_client() and self.there_is_connection:
                    self.open_clients_sockets.remove(self.controller_socket)
                    self.controller_socket = None
                    self.there_is_connection = False


                rlist, wlist, xlist = select.select([self.server_socket] + self.open_clients_sockets, [], [], SELECT_TIMEOUT)
                for current_socket in rlist:
                    if current_socket is self.server_socket:
                        new_socket, address = self.server_socket.accept()
                        self.open_clients_sockets.append(new_socket)
                    elif self.controller_socket is None:
                        id_code = self.com_handler.receive_msg(current_socket)
                        if id_code == self.targetwin.current_id_code:
                            self.controller_socket = current_socket
                            self.messages_to_send.append((self.controller_socket, VALID_CODE_MSG))

                        elif id_code == "":
                            self.open_clients_sockets.remove(current_socket)
                        else:
                            self.messages_to_send.append((current_socket, INVALID_CODE_MSG))
                            self.open_clients_sockets.remove(current_socket)
                    elif current_socket is not self.controller_socket:
                        self.messages_to_send.append((current_socket, UNDER_CONTROL_MSG))
                        self.open_clients_sockets.remove(current_socket)

                self.send_waiting_messages()

    def start_connection(self):
        """
        The function is called when there is a new controller. The function starts the controlling process.
        It sends to the controller the screen size, and than start the receive_screen and stream_screen threads.
        """
        self.com_handler.there_is_a_client = True
        self.there_is_connection = True
        self.com_handler.send_screen_size(self.controller_socket)

        self.stream_thread = threading.Thread(target=self.com_handler.stream_screen, args=[self.controller_socket])
        self.events_thread = threading.Thread(target=self.com_handler.receive_events, args=[self.controller_socket])
        self.stream_thread.start()
        self.events_thread.start()

    def check_if_client(self):
        """
        The function returns whether there is a controlling client or not.
        """
        return self.com_handler.there_is_a_client


class ControlledFrame(wx.Frame):
    def __init__(self, parent, title):
        super(ControlledFrame, self).__init__(parent, title=title, size=CONTROLLED_FRAME_SIZE, style=wx.DEFAULT_FRAME_STYLE ^ wx.MAXIMIZE_BOX ^ wx.RESIZE_BORDER)

        app = wx.GetApp()
        self.md5 = hashlib.md5()
        self.current_id_code = 0
        self.main_panel = None
        self.change_id_code()
        self.main_panel = ControlledPanel(self)
        self.Centre()
        self.Show()
        app.server_manager = ServerThread(self)

        # Start the image_thread thread
        app.server_manager.start()


    def change_id_code(self):
        """
        This function changes the secret code. It generates a random number, and actives the md5 hash function on it,
        in order to get a unique string that includes digits and letters. The function takes only certain part of the
        md5 result string because of its long length. The function is called every certain time.
        """
        change_code_timer = threading.Timer(CODE_CHANGE_DURATION * SECOND_IN_MINUTE, self.change_id_code)
        change_code_timer.daemon = True
        change_code_timer.start()
        self.md5.update(str(random.randint(0, RANDOM_NUM_RANGE)))
        new_code = self.md5.hexdigest()[:LEN_OF_CODE]
        while new_code == self.current_id_code:
            self.md5.update(str(random.randint(0, RANDOM_NUM_RANGE)))
            new_code = self.md5.hexdigest()[:LEN_OF_CODE]

        self.current_id_code = new_code
        if not self.main_panel is None:
            self.main_panel.id_code.SetValue(self.current_id_code)


class ControlledPanel(wx.Panel):
    def __init__(self, parent):
        """
        @parent: the parent Frame object if this panel.
        This function createsqdraws the main panel of the controller, where the user enters the details of the controlled.
        """
        super(ControlledPanel, self).__init__(parent)
        self.image = BACKGROUND_PATH


        bmp1 = wx.Image(self.image, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        # mage's upper left corner anchors at control_panel coordinates (0, 0)
        self.bitmap1 = wx.StaticBitmap(self, -1, bmp1, (0, 0))

        ip_addr = wx.StaticText(self.bitmap1, label=self.get_ip(),
                                style=wx.ALIGN_CENTRE, pos=IP_LABEL_POS, size=IP_LABEL_SIZE)

        self.id_code = wx.TextCtrl(self, value=parent.current_id_code,
                                   style=wx.ALIGN_CENTER_HORIZONTAL | wx.TE_READONLY, pos=CODE_LABEL_POS, size=CODE_LABEL_SIZE)


    @staticmethod
    def get_ip():
        """
        This function returns the IP4V address of the computer.
        """
        addresses = os.popen('IPCONFIG | FINDSTR /R "Ethernet adapter Local Area Connection .* Address.*[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*"')
        first_eth_address = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', addresses.read()).group()

        return first_eth_address



app = ControlledApp()
app.MainLoop()
