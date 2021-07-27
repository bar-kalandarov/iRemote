# -*- coding: utf-8 -*-


class EventMessage(object):
    def __init__(self, event_type, data, x=None, y=None, rotation=None):
        self.event_type = event_type
        if self.event_type == 1:
            self.x = x
            self.y = y
            self.data = data
            self.rotation = rotation
        elif self.event_type == 4:
            self.x = x
            self.y = y
            self.data = data
        else:
            self.data = data

    def to_string(self):
        return "x: " + self.x + ", y: " + self.y