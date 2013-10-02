import time
import os
import sys
import fcntl
from subprocess import *

def _send_cmd(cmd, data):
    pipe.write(cmd + ("%02X" % len(data)) + data)

def _init_module():
    erase()
    global pipe
    pipe = Popen("api/led_server", shell=True, stdin=PIPE).stdin
    _send_cmd("n", "1")
    _send_cmd("o", "43581267" + "65218743")

def _main():
    while 1:
        for i in range(8):
            for j in range(8):
                led.point(x, y)
                led.show()
                time.sleep(0.5);
                led.point(x, y, color=0)

def erase(color=0):
    global fb
    fb = [[color]*8 for i in range(8)]

def point(x, y, color=1):
    fb[x][y] = color;

def show():
    s = ""
    for x in range(8):
        col = 0
        for y in range(8):
            col |= fb[x][y] << (8-y-1)
        s += "%02X" % col
    _send_cmd("m", s);


_init_module()
if __name__ == "__main__":
    _main()

