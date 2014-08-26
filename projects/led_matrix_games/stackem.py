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
from rstem import led_matrix
import RPi.GPIO as GPIO
import sys
import os

class State:
    WIN, LOSE, PLAYING, IDLE, EXIT = range(5)
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
            led_matrix.point(x_start + x_offset, y_start, self.color)
            
    def stop(self):
        """Stops the block from moving"""
        pass
        
    def adjacent(self, other):
        """Returns true if self and other are touching"""
        if (self.origin[0] > (other.origin[0]+other.width))  \
            or ((self.origin[0]+self.width-1) < other.origin[0]):
            return False
        else:
            return True
                    
    def crop(self, other):
        """Returns a block to be the same width x offset of other block"""
        offset = self.origin[0] - other.origin[0]
        loffset = (self.origin[0]+self.width) - (other.origin[0]+other.width)
        if offset >= 0:  # crop rightmost
            self.width = self.width - loffset
            self.origin = self.origin
        elif offset < 0:  # crop left most
            self.width = self.width + offset  # chop off offset amount
            self.origin = [other.origin[0], self.origin[1]]

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

# SETUP ==========================

# setup led matrix
#led_matrix.init_grid(angle=270)
led_matrix.init_matrices([(0,8),(8,8),(8,0),(0,0)])

HEIGHT = led_matrix.height()
WIDTH = led_matrix.width()

# initialize variables
curr_state = State.IDLE  # current state used for state machine
blocks = []              # current block elements on screen
start_width = WIDTH/2           # pixel width of block on start
start_speed = 5           # current speed on start (in pixel/sec)
change_level = int(HEIGHT*(1/3.))  # number of blocks before upping difficulty
curr_width, curr_speed = start_width, start_speed
curr_direction = Direction.RIGHT  # current direction top block is moving

last_input = 1
last_time = 0
locked = False  # spin lock for interrupt handler
button_pressed = False

# helper functions
def draw_blocks():
    """Draws the current blocks on screen"""
    for block in blocks:
        block.draw()

# set up buttons
A = 4
B = 17
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
START = 27
SELECT = 22

def button_handler(channel):
    global curr_state
    global curr_speed
    global curr_width
    global curr_direction
    global blocks
    global button_pressed
    button_pressed = True
    
    # if START pressed exit the game
    if channel == START:
        curr_state = State.EXIT
        return
    
    # else the button must be A
    if curr_state == State.PLAYING:
        # stop the block
        if len(blocks) > 1:
            top_block = blocks[-1]
            base_block = blocks[-2]
            if top_block.adjacent(base_block):
                # crop block only if it hangs off the edge
                if (top_block.origin[0] + top_block.width - 1) > (base_block.origin[0] + base_block.width - 1):
                    blocks[-1].crop(blocks[-2])
            else:
                # top block was not touching bas block, so we lose
                curr_state = State.LOSE
                return
        
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
        led_matrix.erase()
        draw_blocks()
        led_matrix.show()
        curr_state = State.PLAYING

GPIO.setmode(GPIO.BCM)
for but in [A, START]:
    GPIO.setup(but, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(but, GPIO.FALLING, callback=button_handler, bouncetime=300)


        
# State Machine ==================

while True:
    if curr_state == State.IDLE:
        # TODO: display scrollling vertical text 
        text = led_matrix.LEDText("STACK-EM", font_name="large")
        x_pos = led_matrix.width()
        y_pos = led_matrix.height()/2 - text.width/2
        while x_pos > -text.width:
            if state != State.IDLE:
                break
            led_matrix.erase()
            led_matrix.sprite(text, (x_pos, y_pos))
            led_matrix.show()
            x_pos -= 1
            time.sleep(.1)

    elif curr_state == State.PLAYING:
        # show the blocks
        led_matrix.erase()
        draw_blocks()
        led_matrix.show()
        time.sleep(1.0/curr_speed)
    
#            global button_pressed
        if not button_pressed:  # skip moving the block if button pressed
            # change direction if hit edge of screen
            if curr_direction == Direction.RIGHT:
                if blocks[-1].origin[0] + blocks[-1].width == WIDTH:
                    curr_direction = Direction.LEFT
            elif blocks[-1].origin[0] == 0:
                curr_direction = Direction.RIGHT
                
            # move top block in curr_direction at curr_speed
            blocks[-1].move(curr_direction)
        
    elif curr_state == State.WIN:
        led_matrix.erase()
        led_matrix.text("WIN!")
        led_matrix.show()

    elif curr_state == State.LOSE:
        # blink failing block
        blocks[-1].color = 0
        led_matrix.erase()
        draw_blocks()
        led_matrix.show()
        time.sleep(.2)
        led_matrix.erase()
        blocks[-1].color = 0xF
        draw_blocks()
        led_matrix.show()
        time.sleep(.2)

    elif curr_state == State.EXIT:
        led_matrix.cleanup()
        GPIO.cleanup()
        sys.exit(0)

    else:
        raise RuntimeError("Invalid State")
        
#        global button_pressed
    button_pressed = False
    
    


