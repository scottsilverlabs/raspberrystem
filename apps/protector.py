import time
import random
import led
import accel
import gpio
from collections import deque

POLL_PERIOD=0.020
SHOOT=2
LEFT=3
DOWN=4
UP=14
RIGHT=15

WIDTH=led.width()
HEIGHT=led.height()
MISSILE_RATE=10
ENEMY_RATE=10

wall_params = [
    {
        # WALL_SCENE 0
        "more_cols_min":5,
        "more_cols_max":8,
        "tunnel_min":4,
        "tunnel_max":HEIGHT - 3,
        "start_rate":2,
        "period":5,
    }, {
        # WALL_SCENE 1
        "more_cols_min":3,
        "more_cols_max":6,
        "tunnel_min":2,
        "tunnel_max":HEIGHT - 4,
        "start_rate":3,
        "period":5,
    }, {
        # WALL_SCENE 2
        "more_cols_min":3,
        "more_cols_max":5,
        "tunnel_min":2,
        "tunnel_max":HEIGHT - 5,
        "start_rate":5,
        "period":5,
    }
]

no_wall_params = {
    "more_cols_min":2,
    "more_cols_max":2,
    "tunnel_min":HEIGHT,
    "tunnel_max":HEIGHT,
    "start_rate":0,
    "period":0,
}

def clamp(val, minimum, maximum):
    return min(maximum, max(minimum, val))

def randint(min, max):
    return int(random.random() * (max - min + 1)) + min

class AddableTuple(tuple):
    def __add__(self, a):
        return self.__class__([sum(t) for t in zip(self, a)])

class Sprite(object):
    def __init__(self, origin=(0,0), rate=999, width=1, height=1, color=1, collideswith=None):
        self.origin = AddableTuple(origin)
        self.rate = rate
        self.width = width
        self.height = height
        self.color = color
        self.tick = 0
        self.__collided = None
        self.__collideswith = collideswith if collideswith else []
        self.start_time = time.time()

    def check_for_collisions(self):
        for other in self.__collideswith:
            collided = self.collision(other)
            if collided:
                s1, s2 = collided
                s1.__collided = collided
                s2.__collided = collided
                s1.impact(s2)
                s2.impact(s1)

    def trystep(self):
        if self.tick > 1/(self.rate*POLL_PERIOD):
            self.tick = 0
            self.step()
            self.check_for_collisions()
        self.tick += 1
        return self

    def step(self):
        pass

    def impact(self, other):
        pass

    def offscreen(self):
        x, y = self.origin
        return not (0 <= x < WIDTH and 0 <= y < HEIGHT)

    def collideswith(self, *args):
        self.__collideswith = args

    def collided(self):
        return bool(self.__collided)

class SpriteGroup(object):
    def __init__(self, num=0, **kwds):
        self.sprites = []
        for i in range(num):
            self.new(**kwds)
        self.__collideswith = []

    def trystep(self):
        for i, s in enumerate(self.sprites):
            s.trystep()
            if s.offscreen() or s.collided():
                del self.sprites[i]

    def draw(self):
        for s in self.sprites:
            s.draw()

    def __len__(self):
        return len(self.sprites)

    def __getitem__(self, index):
        return self.sprites[index]

    def collision(self, other):
        for s in self.sprites:
            if s.collision(other):
                return (s, other)
        return None

    def collideswith(self, *args):
        self.__collideswith = args

    def getcollideswith(self):
        return self.__collideswith

class PointSprite(Sprite):
    def draw(self):
        led.point(self.origin, color=self.color)

    def collision(self, other):
        if isinstance(other, PointSprite):
            return (self, other) if self.origin == other.origin else None
        else:
            return other.collision(self)
    
class MoveablePointSprite(PointSprite):
    change = {
        LEFT    : (-1,0),
        RIGHT   : (+1,0),
        UP      : (0,+1),
        DOWN    : (0,-1),
    }

    def __init__(self, *args, **kwds):
        self.dirq = deque()
        super(MoveablePointSprite, self).__init__(*args, **kwds)

    def step(self):
        for d in range(len(self.dirq)):
            self.adjust(self.dirq.popleft())

    def adjust(self, direction):
        self.origin += self.change[direction]

    def deferred_adjust(self, direction):
        self.dirq.append(direction)
    
class Wall(Sprite):
    def __init__(self):
        self.set_params()
        self.wall = [(0, HEIGHT - 1) for i in range(WIDTH)]
        self.start_time = time.time()
        super(Wall, self).__init__(rate=self.start_rate)

    def set_params(self, more_cols_min=3, more_cols_max=6, tunnel_min=3, tunnel_max=6, start_rate=3, period=5):
        self.more_cols_min = more_cols_min
        self.more_cols_max = more_cols_max
        self.tunnel_min = tunnel_min
        self.tunnel_max = tunnel_max
        if start_rate > 0:
            self.start_rate = start_rate
        if period > 0:
            self.period = period

    def step(self):
        self.rate = self.start_rate + int((time.time() - self.start_time)/self.period)
        if len(self.wall) <= WIDTH:
            more_cols = randint(self.more_cols_min, self.more_cols_max)
            tunnel_thickness = randint(self.tunnel_min, self.tunnel_max)
            tunnel_bottom = randint(0, HEIGHT - tunnel_thickness)
            tunnel_top = tunnel_bottom + tunnel_thickness - 1
            old_bottom, old_top = self.wall[-1]
            def create_cols(old, new, more_cols):
                diff = abs(old - new)
                if new > old:
                    return [min(new, old + 1 + diff * col / more_cols) for col in range(more_cols)]
                else:
                    return [max(new, old - 1 - diff * col / more_cols) for col in range(more_cols)]
            new_bottoms = create_cols(old_bottom, tunnel_bottom, more_cols)
            new_tops = create_cols(old_top, tunnel_top, more_cols)
            self.wall += zip(new_bottoms, new_tops)
        del self.wall[0]

    def draw(self):
        for x in range(WIDTH):
            for y in range(HEIGHT):
                bottom, top = self.wall[x]
                if y < bottom or y > top:
                    led.point(x, y)

    def collision(self, other):
        if isinstance(other, PointSprite):
            x, y = other.origin
            if 0 <= x < WIDTH:
                bottom, top = wall[x]
                return (self, other) if y < bottom or y > top else None
            return None
        else:
            return other.collision(self)

    def __getitem__(self, index):
        return self.wall[index]
    
class Ship(MoveablePointSprite):
    def __init__(self, origin, color=3):
        super(Ship, self).__init__(origin=origin, color=color)

    def step(self):
        super(Ship, self).step()
        x, y = self.origin
        self.origin = AddableTuple((clamp(x, 0, WIDTH - 1), clamp(y, 0, HEIGHT - 1)))

class Missile(MoveablePointSprite):
    def __init__(self, origin, rate=MISSILE_RATE, color=5, direction=RIGHT, collideswith=None):
        super(Missile, self).__init__(
            origin=origin, rate=rate, color=color, collideswith=collideswith
            )
        self.direction = direction

    def step(self):
        self.adjust(self.direction)
        super(Missile, self).step()

class Missiles(SpriteGroup):
    def __init__(self, direction=RIGHT):
        self.direction = direction
        super(Missiles, self).__init__()

    def new(self, start=(0,0)):
        self.sprites += [Missile(start, direction=self.direction, collideswith=self.getcollideswith())]

class Enemy(MoveablePointSprite):
    def __init__(self, origin, missiles, rate=ENEMY_RATE, color=1, collideswith=None):
        self.missiles = missiles
        super(Enemy, self).__init__(
            origin=origin, rate=rate, color=color, collideswith=collideswith
            )

    def step(self):
        if randint(0,100) > 30:
            self.adjust([LEFT, RIGHT, UP, DOWN][randint(0, 3)])
            x, y = self.origin
            self.origin = AddableTuple((clamp(x, WIDTH/2, WIDTH - 1), clamp(y, 0, HEIGHT - 1)))
        if randint(0,100) > 99:
            self.missiles.new(self.origin)
        super(Enemy, self).step()

class Enemies(SpriteGroup):
    def __init__(self, missiles):
        self.missiles = missiles
        super(Enemies, self).__init__()

    def new(self, num=1):
        start = (WIDTH-1, randint(0, HEIGHT))
        c = self.getcollideswith()
        self.sprites += [Enemy(start, self.missiles, collideswith=c) for i in range(num)]

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

for g in [SHOOT, LEFT, DOWN, UP, RIGHT]:
    gpio.configure(g, gpio.INPUT)

DONE=1
WALL_SCENE=2
WALL_2_ENEMY_SCENE=3
ENEMY_SCENE=4
BIG_BOSS=5
YOU_WIN=6
GAME_OVER=7
while True:
    state = States([WALL_SCENE, WALL_2_ENEMY_SCENE, ENEMY_SCENE] * 3 + [BIG_BOSS, YOU_WIN, GAME_OVER, DONE])
    wall_scene = 0
    enemy_scene = 0

    wall = Wall()
    ship = Ship((2,4))
    missiles = Missiles(direction=RIGHT)
    enemy_missiles = Missiles(direction=LEFT)
    enemies = Enemies(enemy_missiles)
    all_sprites = [wall, ship, missiles, enemies, enemy_missiles]

    wall.collideswith(ship, missiles, enemy_missiles, enemies)
    ship.collideswith(wall, enemies, enemy_missiles)
    missiles.collideswith(wall, enemies)
    enemy_missiles.collideswith(wall, ship)
    enemies.collideswith(wall, ship, missiles)

    next_tick = time.time() + POLL_PERIOD

    while state.current() != DONE:
        if state.current() in [WALL_SCENE, WALL_2_ENEMY_SCENE, ENEMY_SCENE, BIG_BOSS]:
            if state.first_time():
                if state.current() == WALL_SCENE:
                    wall.set_params(**wall_params[wall_scene])
                    wall_scene += 1
                elif state.current() == WALL_2_ENEMY_SCENE:
                    wall.set_params(**no_wall_params)
                elif state.current() == ENEMY_SCENE:
                    wall.set_params(**no_wall_params)
                    enemies.new(5)
                    enemy_scene += 1
                elif state.current() == BIG_BOSS:
                    pass
            else:
                # Adjust sprites based on user input
                clicks = gpio.was_clicked()
                for c in clicks:
                    if c in [LEFT, RIGHT, UP, DOWN]:
                        ship.deferred_adjust(c)
                    if c in [SHOOT]:
                        missiles.new(ship.origin)

                # Move sprites
                for sprite in all_sprites:
                    sprite.trystep()

                # Draw sprites
                led.erase()
                for sprite in all_sprites:
                    sprite.draw()
                led.show()

                # Exit on collision
                if ship.collided():
                    state.skipto(GAME_OVER)

                if state.current() == WALL_SCENE:
                    state.next_if_after(20)
                elif state.current() == WALL_2_ENEMY_SCENE:
                    state.next_if_after(3)
                elif state.current() == ENEMY_SCENE:
                    if len(enemies) == 0:
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

