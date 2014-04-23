import time
import math
from rstem import led

while True:
    led.erase()
    for i in range(16):
        led.line((i,0), (i,8), color=i)
    led.show()
    time.sleep(1)

