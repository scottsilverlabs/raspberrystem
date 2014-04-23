import time
import math
from rstem import led

led.erase()
for row in range(8):
    led.line((0, row), (8, row))
led.show()
