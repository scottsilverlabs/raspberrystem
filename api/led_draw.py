import time
import os
import sys
import fcntl
from led_server import led_server
from led_cal import led_cal
from subprocess import *

class led_draw:
    def __init__(self, server, cal):
        self.server = server
        self.cal = cal

    def bound(self, x, y=None):
        # If y is not given, then x is a tuple of the point
        if y == None:
            x, y = x

        if x >= self.cal.get_fb_width():
            x = self.cal.get_fb_width() - 1
        elif x < 0:
            x = 0

        if y >= self.cal.get_fb_height():
            y = self.cal.get_fb_height() - 1
        elif y < 0:
            y = 0

        return (x, y)

    def sign(self, n):
        return 1 if n >= 0 else -1

    def erase(self, color=0):
        self.fb = [[color]*self.cal.get_fb_height() for i in range(self.cal.get_fb_width())]

    def point(self, x, y=None, color=1):
        # If y is not given, then x is a tuple of the point
        if y == None:
            x, y = x

        # If out of range, its off the screen - just don't display it
        try:
            # Handle negaitive indicies as an exception, because Python
            # supports them
            if x < 0 or y < 0:
                raise IndexError()
            self.fb[int(x)][int(y)] = color;
        except IndexError:
            pass

    def line(self, point_a, point_b, color=1):
        point_a = (int(point_a[0]), int(point_a[1]))
        point_b = (int(point_b[0]), int(point_b[1]))
        x_diff = point_a[0] - point_b[0]
        y_diff = point_a[1] - point_b[1]
        step = self.sign(x_diff) * self.sign(y_diff)
        width = abs(x_diff) + 1
        height = abs(y_diff) + 1
        if (width > height):
            start_point = point_a if x_diff < 0 else point_b
            for x_offset in range(int(width)):
                self.point(
                    start_point[0] + x_offset,
                    start_point[1] + step*(x_offset*height/width),
                    color=color)
        else:
            start_point = point_a if y_diff < 0 else point_b
            for y_offset in range(int(height)):
                self.point(
                    start_point[0] + step*(y_offset*width/height),
                    start_point[1] + y_offset,
                    color=color)
        
    def rect(self, start, dimensions, color=1):
        x, y = start
        width, height = dimensions
        self.line((x, y), (x, y + height), color=color)
        self.line((x, y + height), (x + width, y + height), color=color)
        self.line((x + width, y + height), (x + width, y), color=color)
        self.line((x + width, y), (x, y), color=color)

    def show(self):
        for m in range(self.cal.get_num_matrices()):
            origin_x, origin_y = self.cal.get_matrix_origin(m)
            s = ""
            for x in range(self.cal.get_matrix_width()):
                for y in range(self.cal.get_matrix_height()):
                    s += hex(self.fb[origin_x + x][origin_y + y])[-1]
            self.server.send_cmd("m", str(m) + s);

