# -*- coding: utf-8 -*-
import threading
import wx

class ImageThread(threading.Thread):
    """Simple thread that sends an update to its
    target window once a second with the new count value.
    """
    def __init__(self, targetwin):
        super(ImageThread, self).__init__()

        # Attributes
        self.targetwin = targetwin
        self.stop = False

    def run(self):
        app = wx.GetApp()
        while not self.stop:

            try:
                image = app.comm_handler.receive_msg()
                if image is None:
                    self.stop = True
                    return
            except Exception as e:
                print e
                break

            if self.targetwin:
                try:
                    wx.CallAfter(self.targetwin.resize, image)
                except:
                    pass

    def Stop(self):
        # Stop the thread
        self.stop = True