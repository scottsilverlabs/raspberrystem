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
START_SCROLL_RATE=3
SCROLL_RATE_PERIOD=5
MISSILE_RATE=10
MORE_COLS_MIN=3
MORE_COLS_MAX=6

for g in [SHOOT, LEFT, DOWN, UP, RIGHT]:
    gpio.configure(g, gpio.INPUT)

class AddableTuple(tuple):
    def __add__(self, a):
        return self.__class__([sum(t) for t in zip(self, a)])

class Sprite(object):
    def __init__(self, origin=(0,0), rate=1, width=1, height=1, color=1):
        self.origin = AddableTuple(origin)
        self.rate = rate
        self.width = width
        self.height = height
        self.color = color
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

class SpriteGroup(object):
    def __init__(self, num=0, **kwds):
        self.sprites = []
        for i in range(num):
            self.new(**kwds)

    def trystep(self):
        for i, m in enumerate(self.sprites):
            m.trystep()
            if m.offscreen():
                del self.sprites[i]

    def draw(self):
        for m in self.sprites:
            m.draw()

    def delete(self, index):
        del self.sprites[index]

    def __getitem__(self, index):
        return self.sprites[index]

class PointSprite(Sprite):
    def draw(self):
        led.point(self.origin, color=self.color)
    
class MoveablePointSprite(PointSprite):
    change = {
        LEFT    : (-1,0),
        RIGHT   : (+1,0),
        UP      : (0,+1),
        DOWN    : (0,-1),
    }

    def adjust(self, direction):
        self.origin += self.change[direction]
    
def randint(min, max):
    return int(random.random() * (max - min + 1)) + min

class Wall(Sprite):
    def __init__(self):
        self.wall = [(0, HEIGHT - 1) for i in range(WIDTH)]
        self.start_rate = START_SCROLL_RATE
        self.period = SCROLL_RATE_PERIOD
        self.start_time = time.time()
        super(self.__class__, self).__init__(rate=self.start_rate)

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
    
class Ship(MoveablePointSprite):
    def __init__(self, origin, color=3):
        super(self.__class__, self).__init__(origin=origin, color=color)

class Missile(MoveablePointSprite):
    def __init__(self, origin, rate=MISSILE_RATE, color=5, direction=RIGHT):
        super(self.__class__, self).__init__(origin=origin, rate=rate, color=color)
        self.direction = direction

    def step(self):
        self.adjust(self.direction)

class Missiles(SpriteGroup):
    def new(self, start=(0,0)):
        self.sprites += [Missile(start)]

class Enemy(MoveablePointSprite):
    def __init__(self, origin, rate=MISSILE_RATE, color=2, direction=RIGHT):
        self.direction = direction
        super(self.__class__, self).__init__(origin=origin, rate=rate)

    def step(self):
        self.adjust(self.direction)

class Enemies(SpriteGroup):
    def new(self):
        self.sprites += [Enemy((WIDTH-1, randint(0, HEIGHT)))]

class States(object):
    def __init__(self, l):
        self.l = l
        self.list_iter = iter(self.l)
        self.next()

    def next(self):
        self._first_time = True
        self.start_time = time.time()
        self._current = self.list_iter.next()

    def current(self):
        return self._current

    def first_time(self):
        ft = self._first_time
        self._first_time = False
        return ft

    def next_if_after(self, duration):
        if time.time() - state.start_time > duration:
            self.next()

    def skipto(self, s):
        while self._current != s:
            self.next()

DONE=1
WALL_SCENE=2
ENEMY_SCENE=3
BIG_BOSS=4
GAME_OVER=5
while True:
    state = States([WALL_SCENE, ENEMY_SCENE] * 3 + [BIG_BOSS, GAME_OVER, DONE])
    wall = Wall()
    ship = Ship((2,4))
    missiles = Missiles()
    enemy_missiles = Missiles()
    next_tick = time.time() + POLL_PERIOD

    while state.current() != DONE:
        if state.current() in [WALL_SCENE, ENEMY_SCENE, BIG_BOSS]:
            if state.first_time():
                if state.current() == WALL_SCENE:
                    enemies = Enemies(0)
                elif state.current() == ENEMY_SCENE:
                    enemies = Enemies(5)
                elif state.current() == BIG_BOSS:
                    pass
            else:
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
                    state.skipto(GAME_OVER)

                # Remove missiles colliding with walls
                for i, m in enumerate(missiles):
                    if m.collision(wall):
                        missiles.delete(i)
                for i, m in enumerate(enemies):
                    if m.collision(wall):
                        missiles.delete(i)

                if state.current() == WALL_SCENE:
                    state.next_if_after(20)
                elif state.current() == ENEMY_SCENE:
                    state.next()
                elif state.current() == BIG_BOSS:
                    state.next()

        elif state.current() == GAME_OVER:
            # TODO - print game over unit button press
            state.next()

        t = next_tick - time.time()
        if t > 0:
            time.sleep(t)
        next_tick += POLL_PERIOD

