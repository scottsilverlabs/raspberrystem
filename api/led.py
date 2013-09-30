import time
import os
import sys
import fcntl
from subprocess import *

def send_cmd(cmd, data):
    pipe.write(cmd + ("%02X" % len(data)) + data)

pipe = Popen("api/led_server", shell=True, stdin=PIPE).stdin
send_cmd("n", "1")
send_cmd("o", "4358126765218743")
while 1:
    for i in range(8):
        for j in range(8):
            s = ("00" * i) + ("%02X" % (1<<j)) + ("00" * (7-i))
            #s = ("00" * i) + "FF" + ("00" * (7-i))
            #s = ("%02X" % (1<<i)) * 8
            send_cmd("m", s);
            time.sleep(0.005);
