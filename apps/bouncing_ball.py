import time
import led
import math

x = 0.0
y = 0.0
xdist = 0.1
ydist = 0.5
period = 0.01
while True:
    led.erase()
    led.point(x, y)
    led.show()
    time.sleep(period);
    x, y = (x+xdist, y+ydist)
    if (x > 8 or x < 0):
        xdist = - xdist
    if (y > 8 or y < 0):
        ydist = - ydist

