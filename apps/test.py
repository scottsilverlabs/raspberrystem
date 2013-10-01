import time
import led

while 1:
    for i in range(8):
        for j in range(8):
            s = ("00" * i) + ("%02X" % (1<<j)) + ("00" * (7-i))
            led._send_cmd("m", s);
            time.sleep(0.05);
