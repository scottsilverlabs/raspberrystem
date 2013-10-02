import time
import led

"""
for i in range(1):
    for x in range(8):
        for y in range(8):
            led.point(x, y)
            led.show()
            time.sleep(0.1);
            led.point(x, y, color=0)
"""

for x1 in range(8):
    for y1 in range(8):
        for x2 in range(8):
            for y2 in range(8):
                led.line((x1,y1), (x2,y2))
                led.show()
                time.sleep(0.005);
                led.erase()
