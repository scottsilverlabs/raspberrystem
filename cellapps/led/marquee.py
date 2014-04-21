import time
import led

top = [(x, 7) for x in range(7)]
right = [(7, 7-y) for y in range(7)]
bottom = [(7-x, 0) for x in range(7)]
left = [(0, y) for y in range(7)]
marquee = top + right + bottom +  left

while True:
    led.erase()
    for i, point in enumerate(marquee):
        if i % 28 < 10:
            led.point(point)
    led.show()
    time.sleep(0.1);
    marquee = marquee[1:] + [marquee[0]]
