from subprocess import *
import os

class LedServer:
    def __init__(self):
        here = os.path.dirname(os.path.realpath(__file__))
        self.pipe = Popen(here + "/led_server", shell=True, stdin=PIPE).stdin

    def send_cmd(self, cmd, data):
        self.pipe.write(cmd + ("%02X" % len(data)) + data)

