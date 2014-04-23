import time
import math
from rstem import led

x = 0.0
y = 0.0
xdist = 0.1
ydist = 0.5
period = 0.01
while True:
    led.erase()
    led.point(int(x), int(y))
    led.show()
    time.sleep(period);
    x, y = (x+xdist, y+ydist)
    if (x >= led.width() or x < 0):
        xdist = - xdist
    if (y >= led.height() or y < 0):
        ydist = - ydist

