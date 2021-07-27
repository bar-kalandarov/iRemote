import socket
LEN_OF_LEN = 10
import select
import wx


class CommHandler(object):
    """

    """
    def __init__(self):
        """
        @address: The IP Address to control on.
        @port: The port to connect to.
        This function creates new CommHandler by the given parameters and connect it to the controlled computer.
        """
        self.socket = socket.socket()
        self.is_listen = True

    def connect(self, ip_addr, port):
        """
        @ip_addr: the ip address to connect to (String)
        @port: the port to connect to (int)
        This function connects the socket object to the wanted sever.
        """
        self.socket.connect((ip_addr, port))

    def send_msg(self, msg):
        """
        @msg: a string to send to the control computer.
        This function send a message to the controlled computer through the socket.
        """
        if self.socket is not None:
            length = str(len(msg)).zfill(LEN_OF_LEN)
            self.socket.send(length)
            self.socket.send(msg)

    def receive_msg_by_length(self, length):
        """
        @length: an integer represents the length of the expected message.
        The function receives a message from the server by the expected length and returns it.
        """
        app = wx.GetApp()
        message = ""
        timeout_in_seconds = 0.1
        try:
            while len(message) < length and self.is_listen:
                ready = select.select([self.socket], [], [], timeout_in_seconds)
                if ready[0]:
                    buf = self.socket.recv(length - len(message))
                    if len(buf) == 0:  # Broken comm_handler!
                            self.socket = None
                            wx.CallAfter(app.OnExit)
                            return None
                    message += buf
        except socket.error as msg:
            self.socket = None
            wx.CallAfter(app.OnExit)
            return None
        if self.is_listen:
            return message
        return None


    def receive_msg(self):
        """
        @control_socket: a Socket object of the controls computer.
        This function receives and returns a message by it's length through the socket.
        """
        length = self.receive_msg_by_length(LEN_OF_LEN)
        if length is None:
            return None
        msg = self.receive_msg_by_length(int(length))


        if msg is None:
            return None
        return msg

