
#import pythoncom
import pyHook
import wx
from EventMessage.EventMessage import EventMessage
import jsonpickle


pyhook_to_pyautogui = {
        "Back": "backspace", "Tab": "tab", "Capital": "capslock", "Lwin": "win", "Escape": "esc", "Space": "space",
        "Return": "enter", "End": "end", "Home": "home", "Insert": "insert", "Delete": "delete", "Prior": "pageup", "Next": "pagedown",
        "Left": "left", "Up": "up", "Right": "right", "Down": "down", "Snapshot": "prntscrn", "Scroll": "scrolllock", "Pause": "pause",
        "Numlock": "numlock", "F1": "f1", "F2": "f2", "F3": "f3", "F4": "f4", "F5": "f5", "F6": "f6", "F7": "f7", "F8": "f8",
        "F9": "f9", "F10": "f10", "F11": "f11", "F12": "f12", "Numpad0": "num0", "Numpad1": "num1", "Numpad2": "num2",
        "Numpad3": "num3", "Numpad4": "num4", "Numpad5": "num5", "Numpad6": "num6", "Numpad7": "num7", "Numpad8": "num8",
        "Numpad9": "num9", "Add": "add", "Subtract": "subtract", "Multiply": "multiply", "Decimal":"decimal", "Apps": "apps",
        "Launch_Mail": "launchmail", "Browser_Home": "browserhome", "Browser_Search": "browsersearch",
        "Volume_Mute": "volumemute", "Volume_Up": "volumeup", "Volume_Down": "volumedown", "Oem_Comma": ",",
        "Oem_Period": ".", "Oem_1": ";", "Oem_2": "/", "Oem_3": "`" ,"Oem_4": "[", "Oem_5": "\\", "Oem_6": "]",
        "Oem_7": "'", "Oem_Minus": "-", "Oem_Plus": "=", "Divide": "divide", "Launch_App1": "launchapp1",
        "Launch_App2": "launchapp2"}

KEYBOARD_EVT_TYPE = 2


class KeyboardHandler(object):
    def __init__(self, window_name):
        self.window_name = window_name
        self.ctrl_is_pressed = False
        self.alt_is_pressed = False
        self.shift_is_pressed = False
        self.winkey_is_pressed = False
        self.key_after_winkey = False
        self.wait_for_alt = False
        self.key_after_alt_shift = False

        self.command_keys = ['Lmenu', 'Rmenu', 'Lcontrol', 'Lshift', 'Rcontrol', 'Rshift', 'Lwin', 'Rwin']
        self.socket = wx.GetApp().comm_handler
        # create a hook manager
        self.hook_manager = pyHook.HookManager()
        # watch for all keyboard events
        self.hook_manager.KeyDown = self.OnKeyboardEvent
        self.hook_manager.KeyUp = self.OnKeyUp


    def start(self):
        # set the hook
        self.hook_manager.HookKeyboard()
        #1701 pythoncom.PumpMessages()

    def OnKeyboardEvent(self, event):
        """
        @event: A keyboard event object
        This function is called when a key in the keyboard is pressed down. The function handles these events and sends
        them to the Controlled.
        """
        if event.WindowName == self.window_name: # Does the event occurred in the controlling frame?
            if event.Key not in self.command_keys:
                keys = []
                if self.ctrl_is_pressed:
                    keys.append("ctrl")
                if self.alt_is_pressed:
                    keys.append("alt")
                if self.shift_is_pressed:
                    keys.append("shift")
                if self.winkey_is_pressed:
                    self.key_after_winkey = True
                    keys.append("win")

                try:
                    keys.append(pyhook_to_pyautogui[event.Key])
                except:
                    keys.append(event.Key.lower())

                if keys == ['alt', 'tab']:
                    self.wait_for_alt = True

                if keys == ['ctrl', 'alt', 'delete']:
                    self.alt_is_pressed = False
                    self.ctrl_is_pressed = False
                    wx.MessageBox("Ctrl + Alt + Delete isn't available.")
                else:
                    msg = EventMessage(KEYBOARD_EVT_TYPE, data=keys)
                    msg = jsonpickle.dumps(msg)
                    self.socket.send_msg(msg)
            else:
                if event.Key == 'Lcontrol' or event.Key == 'Rcontrol':
                    self.ctrl_is_pressed = True
                elif event.Key == 'Lmenu' or event.Key == 'Rmenu':
                    self.alt_is_pressed = True
                elif event.Key == "Lshift" or event.Key == "Rshift":
                    self.shift_is_pressed = True
                else:
                    self.winkey_is_pressed = True

            if event.Key.lower() in ['lshift', 'lwin', 'rwin' 'tab', 'lcontrol', 'rcontrol', 'rmenu', 'lmenu', 'delete', 'escape']:
                #Keys to block:
                return False    # block these keys
            else:
                return True
        else:
            # return True to pass the event to other handlers
            return True


    def OnKeyUp(self, event):
        """
        @event: A keyboard event object
        This function is called when a key in the keyboard is released. The function handles these events and sends
        them to the Controlled.
        """
        if event.WindowName == self.window_name:
        #Does the event occurred in the controlling frame?
            if self.ctrl_is_pressed and (event.Key == "Lcontrol" or event.Key == "Rcontrol"):
                self.ctrl_is_pressed = False

            if self.alt_is_pressed and (event.Key == "Lmenu" or event.Key == "Rmenu"):

                if self.wait_for_alt:
                    msg = EventMessage(KEYBOARD_EVT_TYPE, data=['alt'])
                    msg = jsonpickle.dumps(msg)
                    self.socket.send_msg(msg)
                    self.wait_for_alt = False

                self.alt_is_pressed = False

            if self.shift_is_pressed and (event.Key == "Lshift" or event.Key == "Rshift"):
                self.shift_is_pressed = False

            if self.winkey_is_pressed and (event.Key == "Lwin" or event.Key == "Rwin"):
                if not self.key_after_winkey:
                    msg = EventMessage(KEYBOARD_EVT_TYPE, data=['win'])
                    msg = jsonpickle.dumps(msg)
                    self.socket.send_msg(msg)

                self.key_after_winkey = False
                self.winkey_is_pressed = False

        return True

