import time
import os
import sys
import fcntl
from subprocess import *

pipe = 0

def _send_cmd(cmd, data):
    global pipe
    pipe.write(cmd + ("%02X" % len(data)) + data)

def _init_module():
    global pipe
    pipe = Popen("api/led_server", shell=True, stdin=PIPE).stdin
    _send_cmd("n", "1")
    _send_cmd("o", "43581267" + "65218743")

_init_module()
if __name__ == "__main__":
    while 1:
        for i in range(8):
            for j in range(8):
                s = ("00" * i) + ("%02X" % (1<<j)) + ("00" * (7-i))
                _send_cmd("m", s);
                time.sleep(0.05);
