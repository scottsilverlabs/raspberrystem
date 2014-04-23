import time
from rstem import led

WIDTH=led.width()
HEIGHT=led.height()

for x in range(WIDTH):
    for y in range(HEIGHT):
        for w in range(WIDTH-x):
            for h in range(HEIGHT-y):
                led.erase()
                led.rect((x,y), (w,h))
                led.show()
                time.sleep(0.01);
