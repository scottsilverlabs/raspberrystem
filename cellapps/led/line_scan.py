import time
import led

WIDTH=led.width()
HEIGHT=led.height()

for x1 in range(WIDTH):
    for y1 in range(HEIGHT):
        for x2 in range(WIDTH):
            for y2 in range(HEIGHT):
                led.erase()
                led.line((x1,y1), (x2,y2))
                led.show()
                time.sleep(0.01);
