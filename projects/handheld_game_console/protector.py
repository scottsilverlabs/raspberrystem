#
# Copyright (c) 2014, Scott Silver Labs, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import time
import random
import sys
from rstem import led2
#from rstem import accel
import RPi.GPIO as GPIO
#from rstem import gpio
from collections import deque
#from subprocess import Popen


POLL_PERIOD=0.020
SHOOT=2
LEFT=3
DOWN=4
UP=14
RIGHT=15


WIDTH=0  # will be changed during setup
HEIGHT=0
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
    # TODO: don't know what this does???
    return min(maximum, max(minimum, val))

def randint(min, max):
    return int(random.random() * (max - min + 1)) + min

# Defines the definition of adding two tuples.
class AddableTuple(tuple):
    def __add__(self, a):
        return self.__class__([sum(t) for t in zip(self, a)])

class Sprite(object):
    def __init__(self, origin=(0,0), rate=999, width=1, height=1, color=0xF, collideswith=None):
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
                # notify the sprites that they have been collided
                s1, s2 = collided
                s1.__collided = collided
                s2.__collided = collided
                # define who handled the impact
                handled = s1.impact(s2)
                s2.impact(s1, handled)

    def trystep(self):
        """Moves sprite if clock has hit 0"""
        if self.tick > 1/(self.rate*POLL_PERIOD):
            self.tick = 0
            self.step()
            self.check_for_collisions()
        self.tick += 1
        return self

    def step(self):
        """Overloaded function defined in inherited classes."""
        pass

    def impact(self, other, handled=False):
        return False

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
        # run new function for each sprite in group
        for i in range(num):
            self.new(**kwds)
        self.__collideswith = []

    def trystep(self):
        """Steps each sprite in group and removes the sprite if offscreen or collided"""
        for i, s in enumerate(self.sprites):
            s.trystep()
            if s.offscreen() or s.collided():
                del self.sprites[i]

    def draw(self):
        """Draw each sprite in group on screen."""
        for s in self.sprites:
            s.draw()

    def __len__(self):
        return len(self.sprites)

    def __getitem__(self, index):
        return self.sprites[index]

    def collision(self, other):
        """Returns first collision in groupd of sprites."""
        for s in self.sprites:
            if s.collision(other):
                return (s, other)
        return None

    def collideswith(self, *args):
        """Sets what can collide with sprite group."""
        self.__collideswith = args

    def getcollideswith(self):
        return self.__collideswith

class AudibleSprite(Sprite):
    def impact(self, other, handled=False):
        """Overloaded function to play sound on impact."""
        #os.system("aplay /usr/share/pyshared/pygame/examples/data/boom.wav &")
        return True

class PointSprite(Sprite):
    """A single point of a sprite object in the game"""
    def draw(self):
        led2.point(*self.origin, color=self.color)

    def collision(self, other):
        # if both PointSprites then show if points have collided
        if isinstance(other, PointSprite):
            return (self, other) if self.origin == other.origin else None
        else:
            return other.collision(self)
    
class MoveablePointSprite(PointSprite):
    """Similar to a PointSprite only it can change orgin coordinate"""
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
        """In a step move in all directions allocated in queue"""
        for d in range(len(self.dirq)):
            self.adjust(self.dirq.popleft())

    def adjust(self, direction):
        """Append direction change to current position immediatly."""
        self.origin += self.change[direction]

    def deferred_adjust(self, direction):
        """Add direction to movement queue"""
        self.dirq.append(direction)
    
class Wall(Sprite):
    def __init__(self, color=0xF):
        self.set_params()
        self.wall = [(0, HEIGHT - 1) for i in range(WIDTH)]
        self.start_time = time.time()
        self.color = color
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
        # TODO: is this correct?
        """Create a new column of wall relative to the current column of wall."""
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
        """Draw all columns of wall."""
        for x in range(WIDTH):
            for y in range(HEIGHT):
                bottom, top = self.wall[x]
                if y < bottom or y > top:
                    led2.point(x, y, color=self.color) # draw wall with less brightness

    def collision(self, other):
        """If other element is a PointStripe, check if it hit the wall and return collision.
        Else just return whatever other collision causes"""
        if isinstance(other, PointSprite):
            x, y = other.origin
            if 0 <= x < WIDTH:  # if x is on the board
                bottom, top = self.wall[x]
                return (self, other) if y < bottom or y > top else None
            return None
        else:
            return other.collision(self)

    def __getitem__(self, index):
        return self.wall[index]
    
class Ship(MoveablePointSprite, AudibleSprite):
    def __init__(self, origin, color=0xA):
        super(Ship, self).__init__(origin=origin, color=color)

    def step(self):
        super(Ship, self).step()
        x, y = self.origin
        self.origin = AddableTuple((clamp(x, 0, WIDTH - 1), clamp(y, 0, HEIGHT - 1)))   # ????

class Missile(MoveablePointSprite, AudibleSprite):
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

class Enemy(MoveablePointSprite, AudibleSprite):
    def __init__(self, origin, missiles, rate=ENEMY_RATE, color=1, collideswith=None):
        self.missiles = missiles
        super(Enemy, self).__init__(
            origin=origin, rate=rate, color=color, collideswith=collideswith
            )

    def step(self):
        if randint(0,100) > 30:
            self.adjust([LEFT, RIGHT, UP, DOWN][randint(0, 3)])  # enemies move randomly
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
        self.list_iter = iter(self.l) # set up iterator of states
        self.next()

    def next(self):
        self._first_time = True
        self.start_time = time.time()
        if sys.version_info[0] == 2:
            self._current = self.list_iter.next()
        else:
            self._current = self.list_iter.__next__()

    def current(self):
        return self._current

    def first_time(self):
        """Sets first time to be False and returns previous status"""
        ft = self._first_time
        self._first_time = False
        return ft

    def next_if_after(self, duration):
        """Jumps to next state if certain amount of time has passed,
        else keeps current state.
        """
        if time.time() - self.start_time > duration:
            self.next()

    def skipto(self, s):
        while self._current != s:
            self.next()

# TODO: seperate this protector game from the game engine
def protector(num_rows=1, num_cols=2, angle=180):
    try:
#        music_cmd = "exec mpg123 /usr/share/scratch/Media/Sounds/Music\ Loops/Cave.mp3 -g 50 -l 0"
#        music = Popen(music_cmd, shell=True)

        # set up led matrix
        led2.init_grid(num_rows, num_cols, angle)
        global WIDTH
        global HEIGHT
        WIDTH = led2.width()
        HEIGHT = led2.height()

        # set up states
        DONE=1
        WALL_SCENE=2
        WALL_2_ENEMY_SCENE=3
        ENEMY_SCENE=4
        BIG_BOSS=5
        YOU_WIN=6
        GAME_OVER=7
        state = States(
            [WALL_SCENE, WALL_2_ENEMY_SCENE, ENEMY_SCENE] * 3 + [BIG_BOSS, YOU_WIN, GAME_OVER, DONE])
        wall_scene = 0
        enemy_scene = 0

        wall = Wall(color=0xA)
        ship = Ship((2,4), color=0xF)
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

        # state machine that runs through game
        while state.current() != DONE:
            if state.current() in [WALL_SCENE, WALL_2_ENEMY_SCENE, ENEMY_SCENE, BIG_BOSS]:
                if state.first_time():
                    if state.current() == WALL_SCENE:
                        wall.set_params(**wall_params[wall_scene]) # set parameters of particular wall scene
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
                    # TODO: set up as callback functions instead?
                    for c in [SHOOT, LEFT, DOWN, UP, RIGHT]:
                        if GPIO.input(c) == 1:  # TODO: debounce input
                            if c in [LEFT, RIGHT, UP, DOWN]:
                                ship.deferred_adjust(c)
                            if c in [SHOOT]:
                                missiles.new(ship.origin)
                                
#                    clicks = gpio.was_clicked()
#                    for c in clicks:
#                        if c in [LEFT, RIGHT, UP, DOWN]:
#                            ship.deferred_adjust(c)
#                        if c in [SHOOT]:
#                            missiles.new(ship.origin)

                    # Move sprites
                    for sprite in all_sprites:
                        sprite.trystep()

                    # Draw sprites
                    # TODO: use sprite objects in api to draw sprites or meh?
                    led2.erase()
                    for sprite in all_sprites:
                        sprite.draw()
                    led2.show()

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
                led2.erase()
                led2.text("GAME OVER", font_size="small")
                # TODO: scrolling text
                led2.show()
                state.next()

            t = next_tick - time.time()
            if t > 0:
                time.sleep(t)
            next_tick += POLL_PERIOD

    finally:
#        music.kill()
        led2.shutdown_matrices()

#xbase, ybase =  accel.get_data()
#def balancing_dot():
#    x, y = (4, 4)
#    presses = 0
#    while True:
#        # Adjust sprites based on user input
#        clicks = gpio.was_clicked()
#        for c in clicks:
#            if c in [LEFT, RIGHT, UP, DOWN, SHOOT]:
#                presses += 1
#        if presses > 3:
#            break

#        xaccel, yaccel =  accel.get_data()
#        xchg = (xaccel - xbase)/20.0
#        ychg = (yaccel - ybase)/20.0
#        x, y = led.bound(x + xchg, y + ychg)

#        led.erase()
#        led.point(int(x), int(y))
#        led.show()
#        time.sleep(0.1)

#time.sleep(3)


# set up gpio inputs
GPIO.setmode(GPIO.BCM)
for g in [SHOOT, LEFT, DOWN, UP, RIGHT]:
    GPIO.setup(g, GPIO.IN)
#    gpio.configure(g, gpio.INPUT)

while True:
#    balancing_dot()
    protector()

