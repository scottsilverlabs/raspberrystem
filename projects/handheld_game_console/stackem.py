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

import time
import random # use this?
from rstem import led2
import RPi.GPIO as GPIO

class State:
    WIN, LOSE, PLAYING, IDLE, DONE = range(5)
class Direction:
    LEFT, RIGHT, UP, DOWN = range(4)
    
class Block(object):
    def __init__(self, origin, width, color=0xF):
        self.origin = origin
        self.width = width
        self.color = color
        self.direction = Direction.RIGHT  # start moving to right
        
    def draw(self):
        """Draws block on led matrix display"""
        x_start, y_start = self.origin
        for x_offset in range(self.width):
            led2.point(x_start + x_offset, y_start, self.color)
            
    def stop(self):
        """Stops the block from moving"""
        pass
        
    def adjacent(self, other):
        """Returns true if self and other are touching"""
        pass
        
    def match(self, other):
        """Changes block to be the same width x offset of other block"""
        self.origin = (other.origin[0], self.origin[1])  # set x param to be same
        self.width = other.width
        
    def move(self, direction):
        """Moves block on step in given direction"""
        if direction == Direction.LEFT:
            self.origin = (self.origin[0]-1, self.origin[1])
        elif direction == Direction.RIGHT:
            self.origin = (self.origin[0]+1, self.origin[1])
        elif direction == Direction.UP:
            self.origin = (self.origin[0], self.origin[1]+1)
        elif direction == Direction.DOWN:
            self.origin = (self.origin[0], self.origin[1]-1)
        else:
            raise RuntimeError("Invalid Direction")

try:
    # SETUP ==========================

    # setup gpio buttons
    BUTTON=2  # GPIO pin button is connected to
    def button_handler(channel):
        if channel == BUTTON:
            if curr_state == State.PLAYING:
                # stop the block
                if len(blocks) > 1:
                    if blocks[-1].adjacent(blocks[-2]):
                        blocks[-1].match(blocks[-2])  # make block same size and position
                    else:
                        curr_state = State.LOSE
                        return
                
                # show stopped block for a couple seconds
                draw_blocks()
                led2.show()
                time.sleep(1)
                
                # if hit the ceiling, display win screen 
                if len(blocks) == HEIGHT:
                    curr_state = State.WIN
                    return
                    
                # create new block
                if len(blocks) % change_level == 0:  # check if to up difficulty
                    if curr_width > 1:
                        curr_width -= 1
                    curr_speed += 1  # update current speed
                curr_width = min(blocks[-1].width, curr_width)
                blocks.append(Block((0, blocks[-1].origin[1]+1), curr_width))
                
            elif curr_state in [State.IDLE, State.WIN, State.LOSE]:
                # set up game
                blocks = [Block((0,0), start_width, start_speed)]  # set up first block
                led2.erase()
                draw_blocks()
                led2.show()
                curr_state = State.PLAYING

    GPIO.setmode(GPIO.BCM)
    GPIO.add_event_detect(BUTTON, GPIO.FALLING, callback=button_handler, bouncetime=100)
    
    # setup led matrix
    led2.init_grid(2,1,180)
    HEIGHT = led2.height()
    WIDTH = led2.width()
    
    # initialize variables
    curr_state = State.IDLE  # current state used for state machine
    blocks = []              # current block elements on screen
    start_width = 3           # pixel width of block on start
    start_speed = 2           # current speed on start (in pixel/sec)
    start_level = 1           # level of difficulty to start with 
    change_level = int(HEIGHT*(1/3.))  # number of blocks before upping difficulty
    curr_width, curr_speed = start_width, start_speed
    curr_direction = Direction.RIGHT  # current direction top block is moving

    # helper functions
    def draw_blocks():
        """Draws the current blocks on screen"""
        for block in blocks:
            block.draw()
            
    # State Machine ==================
    
    while curr_state != State.DONE:
        if curr_state == State.IDLE:
            # TODO: do something cooler
            led2.point(0,0)
            led2.point(WIDTH-1,0)
            led2.point(0,HEIGHT-1)
            led2.point(WIDTH-1, HEIGHT-1)
            led2.show()

        elif curr_state == State.PLAYING:
            # change direction if hit edge of screen
            if curr_direction == Direction.RIGHT:
                if blocks[-1].origin[0] + blocks.width == WIDTH-1:
                    curr_direction = Direction.LEFT
            elif blocks[-1].origin[0] == 0:
                curr_direction = Direction.RIGHT
                
            # move top block in curr_direction at curr_speed
            blocks[-1].move(curr_direction)
            led2.erase()
            draw_blocks()
            led2.show()
            time.sleep(1/curr_speed)
            
        elif curr_state == State.WIN:
            led2.erase()
            led2.text("WIN!", font_size="small")
            led2.show()
            time.sleep(3)

        elif curr_state == State.LOSE:
            # blink failing block
            blocks[-1].color = 0
            led2.erase()
            draw_blocks()
            led2.show()
            time.sleep(1)
            led2.erase()
            blocks[-1].color = 0xF
            draw_blocks()
            led2.show()
            time.sleep(1)

        else:
            raise RuntimeError("Invalid State")
        
finally:
    led2.shutdown_matrices()
    GPIO.cleanup()
    
    
    
    
    
    
    
    


