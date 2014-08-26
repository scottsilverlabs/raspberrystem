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

from rstem import led_matrix
import RPi.GPIO as GPIO
import time
import random
import sys

# set up led matrix
#led_matrix.init_grid(2,2)
led_matrix.init_matrices([(0,8),(8,8),(8,0),(0,0)])


# set up buttons
A = 4
B = 17
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
START = 27
SELECT = 22

# set up START and A buttons because those are the only buttons we will be using
GPIO.setmode(GPIO.BCM)
GPIO.setup(A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(START, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def randint(min, max):
    return int(random.random() * (max - min + 1)) + min

class Bird(object):

    def __init__(self, position=[3,3], speed=5, gravity_speed=1, flap_distance=2):
        self.speed = speed
        self.position = position
        self.gravity_speed = gravity_speed
        self.flap_distance = flap_distance
        self.flap_tick = 0
        
    def x(self):
        return self.position[0]
    
    def y(self):
        return self.position[1]
        
    def start_flap(self):
        self.flap_tick = self.flap_distance
        
    def flapping(self):
        return (self.flap_tick > 0)
        
    def flap(self, distance=1):
        self.position[1] += 1
        self.flap_tick -= 1
            
    def fall(self):
        if self.position[1] > 0:
            self.position[1] -= 1
        
    def draw(self):
        led_matrix.point(self.x(), self.y())
        
class Pipe(object):

    def __init__(self, x_position=None, width=2, opening_height=3, opening_location=3):
        if x_position is None:
            self.x_position = led_matrix.width()
        else:
            self.x_position = x_position
        self.width = width
        self.opening_height = opening_height      # height of opening from opening_location
        self.opening_location = opening_location  # y coordinate of opening
            
    def move_left(self, num_pixels=1):
        self.x_position -= num_pixels
        
    def collided_with(self, bird):
        """Checks if bird collided with pipe"""
        if self.x_position < bird.x() < (self.x_position + self.width):
            if (self.opening_location) < bird.y() < (self.opening_location + self.opening_height):
                return False
            else:
                return True
        else:
            return False
        
    def draw(self):
        for offset in range(self.width):
            x = self.x_position + offset
            led_matrix.line((x, 0), (x, self.opening_location-1))
            led_matrix.line((x, self.opening_location + self.opening_height), (x, led_matrix.height()))
            
# initialize variables        
class State():
    RESET, IDLE, PLAYING, END, EXIT = range(5)
  
  
try:
    state = State.RESET
    bird = None
    pipes = []
    pipe_start = 0
    pipe_spacing = 12  # number of cycles between forming another pipe
    pipe_tick = 0
    pipe_clock = 0
    pipe_interval = 2  # the lower the number the faster the pipes
    speed = 7

    def button_handler(channel):
        global state
        if channel == START:
            state = State.EXIT
            return
        if state == State.RESET:
            pass  # do nothing
        elif state == State.IDLE:
            state = State.PLAYING
        elif state == State.PLAYING:
            bird.start_flap()
        elif state == State.END:
            state = State.RESET
            
    # runt button_handler if START or A button is pressed
    GPIO.add_event_detect(A, GPIO.FALLING, callback=button_handler, bouncetime=300)
    GPIO.add_event_detect(START, GPIO.FALLING, callback=button_handler, bouncetime=300)
            
    while True:
        if state == State.RESET:
            bird = None
            bird = Bird()
            pipes = []
            pipe_start = led_matrix.width()
            pipe_clock = 0
            state = State.IDLE
            
        elif state == State.IDLE:
            led_matrix.erase()
            bird.draw()
            led_matrix.show()
            
        elif state == State.PLAYING:
            led_matrix.erase()
        
            # draw pipes
            for pipe in pipes:
                pipe.draw()
                
            # draw bird
            if bird.flapping():
                bird.flap()
            else:
                bird.fall()
            bird.draw()
            
            # display on matrix
            led_matrix.show()
            time.sleep(1./speed)
            
            # move all pipes to the left one at certain interval
            # the certain interval allows the pipes to be slower than the bird
            if pipe_clock % pipe_interval == 0:
                for pipe in pipes:
                    pipe.move_left()
            
            # add a new pipe
            if pipe_clock % pipe_spacing == 0:
                # set hole opening to be random, but not too far away from the previous one
                THRESHOLD = 4
                if len(pipes) != 0:
                    max_opening = min(pipes[-1].opening_location + THRESHOLD, led_matrix.height() - 4)
                    min_opening = max(pipes[-1].opening_location - THRESHOLD, 1)
                else:
                    max_opening = led_matrix.height() - 4
                    min_opening = 1
                opening_location = randint(min_opening, max_opening)
                pipes.append(Pipe(opening_location=opening_location))
                
            # increment pipe_clock indefinitly, (we will never hit the max)
            pipe_clock += 1
            
            # check for collision
            for pipe in reversed(pipes):
                # stop checking when we run off the screen
                if pipe.x_position < 0:
                    break
                if pipe.collided_with(bird):
                    state = State.END
                    break
            
        elif state == State.END:
            # calculate score
            score = sum(1 for pipe in pipes if (pipe.x_position + pipe.width - 1) < bird.position[0])
            led_matrix.erase()
            led_matrix.text(str(score))
            led_matrix.show()
            
        elif state == State.EXIT:
            GPIO.cleanup()
            led_matrix.cleanup()
            sys.exit(0)

finally:
    GPIO.cleanup()
    led_matrix.cleanup()


