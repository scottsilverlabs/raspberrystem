from subprocess import *

class LedServer:
    def __init__(self):
        self.pipe = Popen("api/led_server", shell=True, stdin=PIPE).stdin

    def send_cmd(self, cmd, data):
        self.pipe.write(cmd + ("%02X" % len(data)) + data)

