import time
import random
import led
import accel
import gpio

POLL_PERIOD=0.020
SHOOT=2
LEFT=3
DOWN=4
UP=14
RIGHT=15

WIDTH=led.width()
HEIGHT=led.height()
MAX_TUNNEL_THICKNESS = HEIGHT - 3
START_SCROLL_RATE=2
SCROLL_RATE_PERIOD=10
MORE_COLS_MIN=1
MORE_COLS_MAX=4

for g in [SHOOT, LEFT, DOWN, UP, RIGHT]:
    gpio.configure(g, gpio.INPUT)

class AddableTuple(tuple):
    def __add__(self, a):
        return self.__class__([sum(t) for t in zip(self, a)])

change = {
    LEFT    : AddableTuple((-1,0)),
    RIGHT   : AddableTuple((+1,0)),
    UP      : AddableTuple((0,+1)),
    DOWN    : AddableTuple((0,-1)),
}

def randint(min, max):
    return int(random.random() * (max - min + 1)) + min

def scroll(wall, min_width=4):
    if len(wall) <= WIDTH:
        more_cols = randint(MORE_COLS_MIN, MORE_COLS_MAX)
        tunnel_thickness = randint(2, MAX_TUNNEL_THICKNESS)
        bottom = randint(0, HEIGHT - tunnel_thickness)
        top = bottom + tunnel_thickness - 1
        old_bottom, old_top = wall[-1]
        wall += [
            (
                old_bottom - (old_bottom - bottom) * col / more_cols,
                old_top    - (old_top    - top   ) * col / more_cols
            ) 
            for col in range(more_cols)]
    return wall[1:]

def new_game():
    wall = [(0, HEIGHT - 1) for i in range(WIDTH)]
    ship = AddableTuple((2,4))
    return (ship, wall)

def collision(ship, wall):
    x, y = ship
    bottom, top = wall[x]
    return y < bottom or y > top

ship, wall = new_game()
scroll_tick=0
start_time = time.time()
next_tick = start_time + POLL_PERIOD
missiles = []
while True:
    scroll_rate = START_SCROLL_RATE + int((time.time() - start_time)/SCROLL_RATE_PERIOD)
    if scroll_tick > 1/(scroll_rate*POLL_PERIOD):
        wall = scroll(wall)
        scroll_tick = 0
    else:
        scroll_tick += 1
    clicks = gpio.was_clicked()
    for c in clicks:
        if c in [LEFT, RIGHT, UP, DOWN]:
            ship += change[c]
        """
        if c in [SHOOT]:
            missiles += [ship + (1,0)]
        """
    led.erase()
    for x in range(WIDTH):
        for y in range(HEIGHT):
            bottom, top = wall[x]
            if y < bottom or y > top:
                led.point(x, y)
    led.point(ship, color=3)
    """
    for m in missiles:
        led.point(m, color=5)
    """
    led.show()
    if collision(ship, wall):
        led.point(ship, color=5)
        led.show()
        break
    t = next_tick - time.time()
    if t > 0:
        time.sleep(t)
    else:
        print "TIME: ", t
    next_tick += POLL_PERIOD

while True:
    time.sleep(1)
