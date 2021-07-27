# -*- coding: utf-8 -*-
import wx

class ShapedButton(wx.PyControl):
    def __init__(self, parent, normal, pressed=None, disabled=None, pos=(0, 0), size=(156, 57)):
        super(ShapedButton, self).__init__(parent, -1, style=wx.BORDER_NONE, pos=pos, size=size)
        self.normal = normal
        self.pressed = pressed
        self.disabled = disabled
        #self.region = wx.RegionFromBitmapColour(normal, wx.Colour(0, 0, 0, 0))
        self.region = wx.Region(normal, wx.Colour(0, 0, 0, 0))
        self._clicked = False
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window)
    def DoGetBestSize(self):
        return self.normal.GetSize()
    def Enable(self, *args, **kwargs):
        super(ShapedButton, self).Enable(*args, **kwargs)
        self.Refresh()
    def Disable(self, *args, **kwargs):
        super(ShapedButton, self).Disable(*args, **kwargs)
        self.Refresh()
    def post_event(self):
        event = wx.CommandEvent()
        event.SetEventObject(self)
        event.SetEventType(wx.EVT_BUTTON.typeId)
        wx.PostEvent(self, event)
    def on_size(self, event):
        event.Skip()
        self.Refresh()
    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()
        bitmap = self.normal
        if self.clicked:
            bitmap = self.pressed or bitmap
        if not self.IsEnabled():
            bitmap = self.disabled or bitmap
        dc.DrawBitmap(bitmap, 0, 0)
    def set_clicked(self, clicked):
        if clicked != self._clicked:
            self._clicked = clicked
            self.Refresh()
    def get_clicked(self):
        return self._clicked
    clicked = property(get_clicked, set_clicked)
    def on_left_down(self, event):
        x, y = event.GetPosition()
        if self.region.Contains(x, y):
            self.clicked = True
    def on_left_dclick(self, event):
        self.on_left_down(event)
    def on_left_up(self, event):
        if self.clicked:
            x, y = event.GetPosition()
            if self.region.Contains(x, y):
                self.post_event()
        self.clicked = False
    def on_motion(self, event):
        if self.clicked:
            x, y = event.GetPosition()
            if not self.region.Contains(x, y):
                self.clicked = False
    def on_leave_window(self, event):
        self.clicked = False

def main():
    def on_button(event):
        print 'Button was clicked.'
    app = wx.PySimpleApp()
    frame = wx.Frame(None, -1, 'Shaped Button Demo')
    panel = wx.Panel(frame, -1)
    button = ShapedButton(panel,
        wx.Bitmap('button-normal.png'),
        wx.Bitmap('button-pressed.png'),
        wx.Bitmap('button-disabled.png'))
    button.Bind(wx.EVT_BUTTON, on_button)
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.AddStretchSpacer(1)
    sizer.Add(button, 0, wx.ALIGN_CENTER)
    sizer.AddStretchSpacer(1)
    panel.SetSizer(sizer)
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()