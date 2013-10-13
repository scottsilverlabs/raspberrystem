import time
import led
import math

#led.recalibrate()
while True:
    for row in range(8):
        led.erase()
        led.line((0, row), (8, row))
        led.show()
        time.sleep(0.25)

    for col in range(8):
        led.erase()
        led.line((col, 0), (col, 8))
        led.show()
        time.sleep(0.25)
    break
            

