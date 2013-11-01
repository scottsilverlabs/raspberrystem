import time
import os
import sys
import fcntl
from led_server import led_server
from led_cal import led_cal
from led_draw import led_draw
from subprocess import *

def _init_module():
    server = led_server()
    cal = led_cal(server)
    draw = led_draw(server, cal)
    draw.erase()
    return server, cal, draw

server, cal, draw = _init_module()
show = draw.show
rect = draw.rect
line = draw.line
point = draw.point
bound = draw.bound
erase = draw.erase
width = cal.get_fb_width
height = cal.get_fb_height

def _main():
    while 1:
        for i in range(8):
            for j in range(8):
                led.point(x, y)
                led.show()
                time.sleep(0.5);
                led.point(x, y, color=0)

if __name__ == "__main__":
    _main()

