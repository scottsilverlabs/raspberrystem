import time
import os
import sys

def send_cmd(cmd, data):
    fd.write(cmd + ("%02X" % len(data)) + data)

print "before led_server"
os.system("api/led_server &")
print "led_server started"
fd = open("fifo", "w", 0)
print "open"
send_cmd("n", "1")
send_cmd("o", "4358126765218743")
for i in range(8):
    for j in range(8):
        s = ("00" * i) + ("%02X" % (1<<j)) + ("00" * (7-i))
        #s = ("00" * i) + "FF" + ("00" * (7-i))
        #s = ("%02X" % (1<<i)) * 8
        send_cmd("m", s);
        time.sleep(0.1);
"""
for i in range(8):
    for j in range(8):
        s = ("00" * i) + ("%02X" % (1<<j)) + ("00" * (7-i))
        send_cmd("m", s);
        time.sleep(0.2);
"""
