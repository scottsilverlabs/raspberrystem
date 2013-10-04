import time
import led

for x1 in range(8):
    for y1 in range(8):
        for x2 in range(8):
            for y2 in range(8):
                led.erase()
                led.rect((x1,y1), (x2,y2))
                led.show()
                time.sleep(0.01);
