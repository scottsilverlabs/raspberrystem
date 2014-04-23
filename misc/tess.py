import sys
import random
import time
from rstem import led
from rstem import accel
from rstem import gpio

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
    num_dots = 16

class AddableTuple(tuple):
    def __add__(self, a):
        return self.__class__([sum(t) for t in zip(self, a)])

change = {
    LEFT    : AddableTuple((-1,0)),
    RIGHT   : AddableTuple((+1,0)),
    UP      : AddableTuple((0,+1)),
    DOWN    : AddableTuple((0,-1)),
}

dots = [
    AddableTuple((
        int(random.random()*led.width()),
        int(random.random()*led.height())
        )) 
    for i in range(num_dots)
    ]
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

    xs = [x for x, y in dots]
    uniq_xs = set(xs)
    if len(uniq_xs) == 2:
        col1, col2 = uniq_xs
        col1_ys = [y for x, y in dots if x == col1]
        col2_ys = [y for x, y in dots if x == col2]
        if len(set(col1_ys)) == 8 and len(set(col2_ys)) == 8 and abs(col1 - col2) == 1:
            break
        

    

