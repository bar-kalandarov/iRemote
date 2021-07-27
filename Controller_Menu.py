# -*- coding: utf-8 -*-
import wx

from ControllerManager.ControllerManager import ControllerManager
from CommHandler.CommHandler import CommHandler
from ShapedButton.ShapedButton import ShapedButton


CONTROLLED_PORT = 1700
CONTROLLER_APP_TITLE = "Controller Menu"
CONTROLLER_FRAME_SIZE = (800, 450)

IP_LABEL_POS = (310, 95)
IP_LABEL_SIZE = (150, 25)
CODE_LABEL_SIZE = (150, 25)
CODE_LABEL_POS = (310, 175)
BUTTON_SIZE = (310, 280)
BACKGROUND_PATH = r'Images\Background.png'
BUTTON_NORMAL_PATH = r'Images\button-normal.png'
BUTTON_CLICKED_PATH = r'Images\button-pressed.png'
BUTTON_DISABLED_PATH = r'Images\button-disabled.png'

UNDER_CONTROL_MSG = "Already Controlled"
UNDER_CONTROL_ERROR = "The requested IP is already controlled by someone else. Try again later."
IP_ERROR_TITLE = "IP Error"

INVALID_CODE_MSG = "Incorrect Code"
INVALID_CODE_ERROR = "The code is incorrect. Try Again."
CODE_ERROR_TITLE = "Code Error"

INVALID_IP_ERROR = "This IP address can not be controlled."


class ControllerApp(wx.App):
    def __init__(self):
        super(ControllerApp, self).__init__()
        self.login_frame = ControllerMenu(None, title=CONTROLLER_APP_TITLE)
        self.image_thread = None
        self.clipboard_thread = None
        self.comm_handler = None
        self.image_data = None

        self.SetTopWindow(self.login_frame)
        self.login_frame.Show()
        self.controller_manager = None



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
        if self.image_thread is not None:
            self.image_thread.Stop()
            self.image_thread.join()
            self.image_thread = None
        if self.clipboard_thread is not None:
            self.clipboard_thread.join()
            self.clipboard_thread = None
        if self.comm_handler is not None:
            if self.comm_handler.socket is not None:
                self.comm_handler.socket.close()
        self.comm_handler = None
        if self.login_frame is not None:
            self.login_frame.Destroy()
            self.login_frame = None

        if self.controller_manager is not None:
            #self.controller_manager.Destroy()
            self.controller_manager = None


class ControllerMenu(wx.Frame):
    def __init__(self, parent, title):
        super(ControllerMenu, self).__init__(parent, title=title, size=CONTROLLER_FRAME_SIZE, style=wx.DEFAULT_FRAME_STYLE ^ wx.MAXIMIZE_BOX ^ wx.RESIZE_BORDER)
        #self.controller_manager = None
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.create_main_menu()

    def create_main_menu(self):
        """
        The function creates the main frame.
        """
        image_file = BACKGROUND_PATH
        bmp1 = wx.Image(image_file, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        # mage's upper left corner anchors at control_panel coordinates (0, 0)
        self.bitmap1 = wx.StaticBitmap(self, -1, bmp1, (0, 0))
        #Controlled Details
        #IP
        self.ip = wx.TextCtrl(self.bitmap1, size=IP_LABEL_SIZE, pos=IP_LABEL_POS)

        #Code
        self.id_code = wx.TextCtrl(self.bitmap1, size=CODE_LABEL_SIZE, pos=CODE_LABEL_POS)

        self.connect_button = ShapedButton(self.bitmap1, wx.Bitmap(BUTTON_NORMAL_PATH), wx.Bitmap(BUTTON_CLICKED_PATH), wx.Bitmap(BUTTON_DISABLED_PATH), BUTTON_SIZE)
        self.connect_button.Bind(wx.EVT_BUTTON, self.connect)

    def try_connect(self):
        """
        This function tries to connect to a Controlled server according to the details in the frame of IP and ID Code.
        It also alerts if there is a error in the connection process.
        Returns True if the connection succeed, otherwise returns False;
        """
        app = wx.GetApp()
        try:
            app.comm_handler.connect(self.ip.GetValue(), CONTROLLED_PORT)
        except Exception as e:
            print e
            wx.MessageBox(INVALID_IP_ERROR, IP_ERROR_TITLE)
            return False

        app.comm_handler.send_msg(self.id_code.GetValue())
        response = app.comm_handler.receive_msg()
        if response == INVALID_CODE_MSG:
            wx.MessageBox(INVALID_CODE_ERROR, CODE_ERROR_TITLE)
            return False
        elif response == UNDER_CONTROL_MSG:
            wx.MessageBox(UNDER_CONTROL_ERROR, IP_ERROR_TITLE)
            return False

        return True

    def connect(self, evt):
        """
        This function handles the whole connection process and uses try_connect() function.
        If the connection succed, it closes the current frame and opens the Control screen.
        """
        app = wx.GetApp()
        app.comm_handler = CommHandler()
        succes = self.try_connect()

        if succes:
            app.login_frame.Hide()
            app.controller_manager = ControllerManager(None)
            app.SetTopWindow(app.controller_manager)
            app.controller_manager.Show()
            self.Destroy()
            app.login_frame = None
            app.controller_manager.start()

    def OnClose(self, event):
        """
        This function overrides the OnClose function of wx.Frame.
        It is called when the Frame closes.
        This function handles the closing process properly.
        """
        app = wx.GetApp()
        app.login_frame = None
        event.Skip()



app = ControllerApp()
app.MainLoop()