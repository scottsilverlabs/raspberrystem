import time
import led

while 1:
    for x in range(8):
        for y in range(8):
            led.point(x, y)
            led.show()
            time.sleep(0.1);
            led.point(x, y, color=0)
