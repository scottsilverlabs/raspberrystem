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
        if (self.origin[0] > (other.origin[0]+other.width))  \
            or ((self.origin[0]+self.width-1) < other.origin[0]):
            print("False")
            return False
        else:
            print("True")
            return True
                    
    def crop(self, other):
        """Returns a block to be the same width x offset of other block"""
        offset = self.origin[0] - other.origin[0]
        loffset = (self.origin[0]+self.width) - (other.origin[0]+other.width)
        if offset >= 0:  # crop rightmost
            width = self.width - loffset
            origin = self.origin
        elif offset < 0:  # crop left most
            width = self.width + offset  # chop off offset amount
            origin = [other.origin[0], self.origin[1]]
#            self.origin[0] = other.origin[0] # move to right
        return Block(origin, width)
            
        
#        self.origin = (other.origin[0], self.origin[1])  # set x param to be same
#        self.width = other.width
        
    def move(self, direction):
        """Moves block on step in given direction"""
        if direction == Direction.LEFT:
            self.origin = [self.origin[0]-1, self.origin[1]]
        elif direction == Direction.RIGHT:
            self.origin = [self.origin[0]+1, self.origin[1]]
        elif direction == Direction.UP:
            self.origin = [self.origin[0], self.origin[1]+1]
        elif direction == Direction.DOWN:
            self.origin = [self.origin[0], self.origin[1]-1]
        else:
            raise RuntimeError("Invalid Direction")

try:
    # SETUP ==========================

    # setup led matrix
    led2.init_grid(2,1,270)
    HEIGHT = led2.height()
    WIDTH = led2.width()
    
    # initialize variables
    curr_state = State.IDLE  # current state used for state machine
    blocks = []              # current block elements on screen
    start_width = 3           # pixel width of block on start
    start_speed = 1           # current speed on start (in pixel/sec)
    change_level = int(HEIGHT*(1/3.))  # number of blocks before upping difficulty
    curr_width, curr_speed = start_width, start_speed
    curr_direction = Direction.RIGHT  # current direction top block is moving
    
    last_input = 1
    last_time = 0
    locked = False  # spin lock for interrupt handler
    
    # helper functions
    def draw_blocks():
        """Draws the current blocks on screen"""
        for block in blocks:
            block.draw()

    # setup gpio buttons
    BUTTON=4  # GPIO pin button is connected to
    def button_handler(channel):
        global curr_state
        global curr_speed
        global curr_width
        global curr_direction
        global blocks
        if not locked:
            if curr_state == State.PLAYING:
                # stop the block
                if len(blocks) > 1:
                    if blocks[-1].adjacent(blocks[-2]):
                        blocks[-1] = blocks[-1].crop(blocks[-2])
                    else:
                        curr_state = State.LOSE
                        return
                
                # show stopped block for a couple seconds
                draw_blocks()
                led2.show()
#                time.sleep(1)
                
                # if hit the ceiling, display win screen 
                if len(blocks) == HEIGHT:
                    curr_state = State.WIN
                    return
                    
                # create new block
                if len(blocks) % change_level == 0:  # check if to up difficulty
                    if curr_width > 1:
                        curr_width -= 1
                    curr_speed += 5  # update current speed
                curr_width = min(blocks[-1].width, curr_width)
                blocks.append(Block([0, blocks[-1].origin[1]+1], curr_width))
                
            elif curr_state in [State.IDLE, State.WIN, State.LOSE]:
                # set up game
                blocks = [Block([0,0], start_width)]  # set up first block
                curr_width = start_width
                curr_speed = start_speed
                led2.erase()
                draw_blocks()
                led2.show()
                curr_state = State.PLAYING

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(BUTTON, GPIO.FALLING, callback=button_handler, bouncetime=300)
    

            
    # State Machine ==================
    
    while curr_state != State.DONE:
#        # check if button pressed
#        if (not GPIO.input(BUTTON)) and ((time.time() - last_time) > .3) and (last_input == 1):
#            button_handler(BUTTON)
#            last_time = time.time()
#        last_input = GPIO.input
        
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
                if blocks[-1].origin[0] + blocks[-1].width == WIDTH:
                    curr_direction = Direction.LEFT
            elif blocks[-1].origin[0] == 0:
                curr_direction = Direction.RIGHT
                
            # move top block in curr_direction at curr_speed
            locked = True
            blocks[-1].move(curr_direction)
            locked = False
            led2.erase()
            draw_blocks()
            led2.show()
            time.sleep(1/curr_speed)
            
        elif curr_state == State.WIN:
            print("IN WIN")
            led2.erase()
            led2.text("WIN!", font_size="small")
            led2.show()
            time.sleep(1)

        elif curr_state == State.LOSE:
            # blink failing block
            print("IN LOSE")
            blocks[-1].color = 0
            led2.erase()
            draw_blocks()
            led2.show()
            time.sleep(.2)
            led2.erase()
            blocks[-1].color = 0xF
            draw_blocks()
            led2.show()
            time.sleep(.2)

        else:
            raise RuntimeError("Invalid State")
        
finally:
    led2.shutdown_matrices()
    GPIO.cleanup()
    
    
    
    
    
    
    
    


