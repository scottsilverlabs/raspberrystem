import time
from rstem import led
from rstem import accel

xbase, ybase =  accel.get_data()
x, y = (led.width()/2, led.height()/2)
while True:
    xaccel, yaccel =  accel.get_data()
    xchg = (xaccel - xbase)/20.0
    ychg = (yaccel - ybase)/20.0
    x, y = led.bound(int(x + xchg), int(y + ychg))

    led.erase()
    led.point(x, y)
    led.show()
    time.sleep(0.1);
