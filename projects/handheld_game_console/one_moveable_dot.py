import time
from rstem import led
from rstem import accel
from rstem import gpio

POLL_PERIOD=0.010
LEFT=3
DOWN=4
UP=14
RIGHT=15

for g in [LEFT, DOWN, UP, RIGHT]:
    gpio.configure(g, gpio.INPUT)

x, y = 5, 5
while True:
    clicks = gpio.was_clicked()
    if LEFT in clicks:
            x -= 1
    if RIGHT in clicks:
            x += 1
    if DOWN in clicks:
            y -= 1
    if UP in clicks:
            y += 1
    led.erase()
    led.point(x, y)
    led.show()
    time.sleep(POLL_PERIOD)
    
