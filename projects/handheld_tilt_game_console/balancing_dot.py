import time
from rstem import led
from rstem import accel

xbase, ybase =  accel.get_data()
x, y = (4, 4)
while True:
    xaccel, yaccel =  accel.get_data()
    xchg = (xaccel - xbase)/20.0
    ychg = (yaccel - ybase)/20.0
    x, y = led.bound(x + xchg, y + ychg)

    led.erase()
    led.point(x, y)
    led.show()
    time.sleep(0.1);
