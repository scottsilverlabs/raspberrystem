import sys
import time
import led
import accel
import gpio

POLL_PERIOD=0.010
SHOOT=2
LEFT=3
DOWN=4
UP=14
RIGHT=15

for g in [SHOOT, LEFT, DOWN, UP, RIGHT]:
    gpio.configure(g, gpio.INPUT)

try:
    num_dots = int(sys.argv[1])
except:
    num_dots = 3

class AddableTuple(tuple):
    def __add__(self, a):
        return self.__class__([sum(t) for t in zip(self, a)])

change = {
    LEFT    : AddableTuple((-1,0)),
    RIGHT   : AddableTuple((+1,0)),
    UP      : AddableTuple((0,+1)),
    DOWN    : AddableTuple((0,-1)),
}

dots = [AddableTuple((0,0)) for i in range(num_dots)]
current_dot = 0
while True:
    clicks = gpio.was_clicked()
    for c in clicks:
        if c in [LEFT, RIGHT, UP, DOWN]:
            dots[current_dot] += change[c]
        if c == SHOOT:
            current_dot = (current_dot + 1) % num_dots
    led.erase()
    for i, d in enumerate(dots):
        if i == current_dot:
            continue
        led.point(dots[i], color=1)
    led.point(dots[current_dot], color=3)
    led.show()
    time.sleep(POLL_PERIOD)
    
