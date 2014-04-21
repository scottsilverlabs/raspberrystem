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
MIN_TUNNEL_THICKNESS = 2
MAX_TUNNEL_THICKNESS = HEIGHT - 4
START_SCROLL_RATE=2
SCROLL_RATE_PERIOD=10
MISSILE_RATE=10
MORE_COLS_MIN=2
MORE_COLS_MAX=5

for g in [SHOOT, LEFT, DOWN, UP, RIGHT]:
    gpio.configure(g, gpio.INPUT)

class AddableTuple(tuple):
    def __add__(self, a):
        return self.__class__([sum(t) for t in zip(self, a)])

class Sprite(object):
    def __init__(self, origin=(0,0), rate=1, width=1, height=1):
        self.origin = AddableTuple(origin)
        self.rate = rate
        self.width = width
        self.height = height
        self.tick = 0
        self.start_time = time.time()

    def trystep(self):
        if self.tick > 1/(self.rate*POLL_PERIOD):
            self.tick = 0
            self.step()
        self.tick += 1
        return self

    def step(self):
        pass

    def offscreen(self):
        x, y = self.origin
        return not (0 < x < WIDTH and 0 < y < HEIGHT)

    def collision(self, other):
        if type(other) == Wall:
            x, y = self.origin
            bottom, top = wall[x]
            return y < bottom or y > top
        else:
            return self.origin == other.origin
    
def randint(min, max):
    return int(random.random() * (max - min + 1)) + min

class Wall(Sprite):
    def __init__(self):
        self.wall = [(0, HEIGHT - 1) for i in range(WIDTH)]
        self.start_rate = START_SCROLL_RATE
        self.period = SCROLL_RATE_PERIOD
        self.start_time = time.time()
        super(Wall, self).__init__(rate=self.start_rate)

    def step(self):
        self.rate = self.start_rate + int((time.time() - self.start_time)/self.period)
        if len(self.wall) <= WIDTH:
            more_cols = randint(MORE_COLS_MIN, MORE_COLS_MAX)
            tunnel_thickness = randint(MIN_TUNNEL_THICKNESS, MAX_TUNNEL_THICKNESS)
            bottom = randint(0, HEIGHT - tunnel_thickness)
            top = bottom + tunnel_thickness - 1
            old_bottom, old_top = self.wall[-1]
            self.wall += [
                (
                    old_bottom - (old_bottom - bottom) * col / more_cols,
                    old_top    - (old_top    - top   ) * col / more_cols
                ) 
                for col in range(more_cols)]
        del self.wall[0]

    def draw(self):
        for x in range(WIDTH):
            for y in range(HEIGHT):
                bottom, top = self.wall[x]
                if y < bottom or y > top:
                    led.point(x, y)

    def __getitem__(self, index):
        return self.wall[index]
    
class Ship(Sprite):
    change = {
        LEFT    : (-1,0),
        RIGHT   : (+1,0),
        UP      : (0,+1),
        DOWN    : (0,-1),
    }

    def adjust(self, direction):
        self.origin += self.change[direction]

    def draw(self):
        led.point(self.origin, color=3)

class Missile(Sprite):
    def __init__(self, origin, rate=MISSILE_RATE):
        super(Missile, self).__init__(origin=origin, rate=rate)

    def step(self):
        self.origin += (1,0)

    def draw(self):
        led.point(self.origin, color=5)

class Missiles:
    def __init__(self, rate):
        self.missiles = []

    def trystep(self):
        for i, m in enumerate(self.missiles):
            m.trystep()
            if m.offscreen():
                del self.missiles[i]

    def draw(self):
        for m in self.missiles:
            m.draw()

    def new(self, start):
        self.missiles += [Missile(start + (1,0))]

    def delete_collisions(self, wall):
        for i, m in enumerate(self.missiles):
            if m.collision(wall):
                del self.missiles[i]

    def __getitem__(self, index):
        return self.missiles[index]
    

wall = Wall()
ship = Ship((2,4))
missiles = Missiles(MISSILE_RATE)
next_tick = time.time() + POLL_PERIOD
while True:
    # Adjust sprites based on user input
    clicks = gpio.was_clicked()
    for c in clicks:
        if c in [LEFT, RIGHT, UP, DOWN]:
            ship.adjust(c)
        if c in [SHOOT]:
            missiles.new(ship.origin)

    # Move background and sprites
    for sprite in [wall, ship, missiles]:
        sprite.trystep()

    # Draw background and sprites
    led.erase()
    for sprite in [wall, ship, missiles]:
        sprite.draw()
    led.show()

    # Exit on collision
    if ship.collision(wall):
        led.point(ship.origin, color=5)
        led.show()
        break

    # Remove missiles colliding with walls
    missiles.delete_collisions(wall)

    t = next_tick - time.time()
    if t > 0:
        time.sleep(t)
    next_tick += POLL_PERIOD

while True:
    time.sleep(1)
