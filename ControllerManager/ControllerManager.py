##
import pyautogui
import sys
from CommHandler.CommHandler import CommHandler
from EventMessage.EventMessage import EventMessage
import wx
import time
import threading
from threading import Timer
import cStringIO
import math
import jsonpickle
import os
from KeyboardEventsHandler.KeybaordEventsHandler import KeyboardHandler

import subprocess
from ImageThread.ImageThread import ImageThread
import win32clipboard
import numpy

PROGRAM_TITLE = "Remote Control"

LOADING_IMAGE_DIR = sys.argv[0][:sys.argv[0].rfind("\\")+1] + r"Images\LoadingScreen.png"
CONTROLLED_PORT = 1700


SCROLL_MOUSE_EVT = "scroll"
LEFT_DOWN_EVT = "left down"
LEFT_UP_EVT = "left up"
RIGHT_DOWN_EVT = "right down"
RIGHT_UP_EVT = "right up"
MOVE_MOUSE_EVT = "move"
MIDDLE_DOWN_EVT = "middle down"
MIDDLE_UP_EVT = "middle up"
CONTROLLER_FRAME_SIZE = (1000, 800)
MOUSE_EVT_TYPE = 1
CLIPBOARD_EVT_TYPE = 3
FILE_EVT_TYPE = 4

NEW_IMAGE_PATH = "image.png"
SEND_MOUSE_POS_DURATION = 0.1 # Seconds
CLIPBOARD_CHECK_SLEEP_TIME = 0.1 # Seconds

########################################################################
class MyFileDropTarget(wx.FileDropTarget):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, window):
        """Constructor"""
        wx.FileDropTarget.__init__(self)
        self.window = window

    #----------------------------------------------------------------------
    def OnDropFiles(self, x, y, filesnames):
        """
        @x: indicates the X axis of the position where the file was dropped.
        @x: indicates the Y axis of the position where the file was dropped.
        @filesnames: a list that includes the names of the files that have been dropped.
        This function handles file dropping events. It reads the dropped file name, and send to the Controlled
        a EventMessage that includes the position, the file content and its name.
        """
        x = float(x) / (float(self.window.current_size[0]) / float(self.window.controlled_screen_width))
        y = float(y) / (float(self.window.current_size[1]) / float(self.window.controlled_screen_height))
        x = int(math.floor(x))
        y = int(math.floor(y))

        my_file = open(filesnames[0], "rb")
        content = my_file.read()
        file_name = os.path.basename(filesnames[0])

        msg = EventMessage(FILE_EVT_TYPE, [file_name, content], x, y)
        msg = jsonpickle.dumps(msg)
        self.window.comm_handler.send_msg(msg)


########################################################################

class ControllerManager(wx.Frame):
    def __init__(self, parent, redirect=False, filename=None):
        super(ControllerManager, self).__init__(parent, title=PROGRAM_TITLE, size=CONTROLLER_FRAME_SIZE)

        app = wx.GetApp()
        app.image_thread = ImageThread(self)
        self.comm_handler = app.comm_handler
        self.image_loaded = False
        self.time_to_send_pos = True
        self.current_size = self.GetSize()

        app.clipboard_thread = threading.Thread(target=self.clipbaord_changes)

        self.control_panel = wx.Panel(self)
        self.control_panel.Bind(wx.EVT_SIZE, self.on_resize)
        self.createWidgets()

        self.imageCtrl.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_press)
        self.imageCtrl.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_scroll)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        file_drop_target = MyFileDropTarget(self)
        self.SetDropTarget(file_drop_target)

    def start(self):
        """
        This function starts all the threads in the controlling process: Receiving the screen streaming, checking the
        clipboard, check for keyboard events.
        It also receives the Controlled screen size.
        """
        app = wx.GetApp()
        self.receive_screen_size()

        # Start the image_thread thread
        app.image_thread.start()
        app.clipboard_thread.start()

        self.keyboardEventsHandler = KeyboardHandler(PROGRAM_TITLE)
        self.keyboardEventsHandler.start()


    def createWidgets(self):
        """
        This function creates/draws the controlling panel.
        """
        app = wx.GetApp()
        app.image_data = open(LOADING_IMAGE_DIR, "rb").read()

        img = self.scale_image(app.image_data)
        self.imageCtrl = wx.StaticBitmap(self.control_panel, wx.ID_ANY,
                                         wx.BitmapFromImage(img))

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.imageCtrl, 0, wx.ALL, 0)
        self.control_panel.SetSizer(self.mainSizer)

        self.control_panel.Layout()
        self.image_loaded = True

    def on_resize(self, event):
        """
        This function is called when the controlling frame is resized by the user.
        """
        app = wx.GetApp()
        if self.image_loaded:
            self.resize(app.image_data)

    def resize(self, image):
        """
        @image: a binary image data.
        This function handles case in which the controlling frame is resized. It changes the stream screen so it will fit
        the current frame size.
        """
        app = wx.GetApp()
        try:
            if not app.image_thread.stop:
                app.image_data = image
                self.image_data = image
                self.current_size = self.control_panel.GetSize()
                img = self.scale_image(image)
                self.imageCtrl.SetBitmap(wx.BitmapFromImage(img))
                self.control_panel.Refresh()
                self.control_panel.Layout()

        except Exception as e:
            print e

    def scale_image(self, image):
        """
        @image: a binary image data.
        This function receives a image data and creates the same image but in the size of the controlling frame size,
        and returns the new image.
        """
        # convert to a data stream
        stream = cStringIO.StringIO(image)
        # convert to a image
        fd = open(NEW_IMAGE_PATH, 'wb')
        fd.write(image)
        fd.close()
        img = wx.ImageFromStream(stream)

        try:
            img = img.Scale(self.current_size.GetWidth(), self.current_size.GetHeight(), wx.IMAGE_QUALITY_HIGH)
        except Exception as e:
            print e

        return img

    def on_mouse_press(self, event):
        """
        @event: a mouse event object.
        This function handles and sends to the Controlled all kind of mouse events that are been detected.
        """
        if event.Dragging() and self.time_to_send_pos:
            self.time_to_send_pos = False
            x, y = self.get_mouse_position(event)
            self.send_mouse_click(x, y, MOVE_MOUSE_EVT)
            Timer(SEND_MOUSE_POS_DURATION, self.change_send_pos).start()

        if event.Moving() and self.time_to_send_pos:
            self.time_to_send_pos = False
            x, y = self.get_mouse_position(event)
            self.send_mouse_click(x, y, MOVE_MOUSE_EVT)
            Timer(SEND_MOUSE_POS_DURATION, self.change_send_pos).start()

        if event.LeftDClick():
            x, y = self.get_mouse_position(event)
            self.send_mouse_click(x, y, LEFT_DOWN_EVT)

        if event.LeftDown():
            x, y = self.get_mouse_position(event)
            self.send_mouse_click(x, y, LEFT_DOWN_EVT)

        if event.LeftUp():
            x, y = self.get_mouse_position(event)
            self.send_mouse_click(x, y, LEFT_UP_EVT)

        if event.RightDown():
            x, y = self.get_mouse_position(event)
            self.send_mouse_click(x, y, RIGHT_DOWN_EVT)

        if event.RightUp():
            x, y = self.get_mouse_position(event)
            self.send_mouse_click(x, y, RIGHT_UP_EVT)

        if event.MiddleDown():
            x, y = self.get_mouse_position(event)
            self.send_mouse_click(x, y, MIDDLE_DOWN_EVT)

        if event.MiddleUp():
            x, y = self.get_mouse_position(event)
            self.send_mouse_click(x, y, MIDDLE_UP_EVT)

    def on_mouse_scroll(self, event):
        """
        @event: a mouse scroll event object.
        This function sends to the Controlled mouse scroll events.
        """
        self.send_mouse_click(None, None, SCROLL_MOUSE_EVT, event.GetWheelRotation())

    def send_mouse_click(self, x, y, event_str, rotation=0):
        """
        @x: The X coordinate of the mouse event.
        @y: The Y coordinate of the mouse event.
        @event_str: The type of mouse events (Right mouse up, left mouse down and etc.).
        @rotation: Indicates if the mouse was scrolled up (1) or down(-1). Default value is 0 for no scrolling.
        """
        msg = EventMessage(MOUSE_EVT_TYPE, event_str, x, y, rotation)
        msg = jsonpickle.dumps(msg)
        self.comm_handler.send_msg(msg)
        self.double_click = False

    def get_mouse_position(self, event):
        """
        @event: a mouse event object.
        This function returns the X and Y coordinates of the received mouse event (int).
        """
        x, y = numpy.array(event.GetPosition())
        x = float(x) / (float(self.current_size[0]) / float(self.controlled_screen_width))
        y = float(y) / (float(self.current_size[1]) / float(self.controlled_screen_height))
        x = int(math.floor(x))
        y = int(math.floor(y))
        return x, y

    def change_send_pos(self):
        """
        This function changes the flag which indicates whether it is time to send the mouse position to the controlled,
        or not. This function is called every certain time.
        """
        self.time_to_send_pos = True

    def receive_screen_size(self):
        """
        This function receives the details of the Controlled screen: Its weight and height. This function is called once,
        when the controlling process is started.
        """
        self.controlled_screen_height = int(self.comm_handler.receive_msg())
        self.controlled_screen_width = int(self.comm_handler.receive_msg())

    def OnClose(self, event):
        """
        This function overrides the OnClose function of wx.Frame class. It is called when the frame is closed, and handles
        the closing process properly.
        """
        app = wx.GetApp()
        app.controller = None
        event.Skip()

    def clipbaord_changes(self):
        """
        This function detects, handles and sends any clipboard event - when a new content is copied.
        It repeats itself until the controlling process ends.
        """
        app = wx.GetApp()
        win32clipboard.OpenClipboard()
        temp_data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        while app.image_thread is not None:
            win32clipboard.OpenClipboard()
            current_data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            if not current_data == temp_data:
                msg = EventMessage(CLIPBOARD_EVT_TYPE, data=current_data)
                msg = jsonpickle.dumps(msg)
                self.comm_handler.send_msg(msg)
                temp_data = current_data
            time.sleep(CLIPBOARD_CHECK_SLEEP_TIME)



#my_app = PhotoCtrl()
#my_app.MainLoop()
