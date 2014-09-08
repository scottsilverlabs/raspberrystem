#!/usr/bin/env python3

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
import sys
from rstem import led_matrix

# notify of progress
print("P25")
sys.stdout.flush()

import RPi.GPIO as GPIO
import os

# notify of progress
print("P50")
sys.stdout.flush()

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
        self.moving = True
        
    def draw(self):
        """Draws block on led matrix display"""
        x_start, y_start = self.origin
        for x_offset in range(self.width):
            led_matrix.point(x_start + x_offset, y_start, self.color)
            
    def stop(self):
        """Stops the block from moving"""
        self.moving = False
        
    def adjacent(self, other):
        """Returns true if self and other are touching"""
        if (self.origin[0] > (other.origin[0]+other.width-1))  \
            or ((self.origin[0]+self.width-1) < other.origin[0]):
            return False
        else:
            return True
                    
    def crop(self, other):
        """Crops off the left or right of the self block to match the other block"""
        # number of pixels overhanging on the left (if any)
        left_overhang = other.origin[0] - self.origin[0]
        if left_overhang > 0:
            self.width -= left_overhang
            self.origin = (other.origin[0], self.origin[-1])  # match other in x position
            return
        
        right_overhang = (self.origin[0]+self.width) - (other.origin[0]+other.width)
        if right_overhang > 0:
            self.width -= right_overhang
            return
        
        
        
#        offset = self.origin[0] - other.origin[0]
#        loffset = (other.origin[0]+other.width) - (self.origin[0]+self.width) 
#        if offset >= 0:  # crop rightmost
#            self.width = self.width - loffset
#            self.origin = self.origin
#        elif loffset > 0:  # crop left most
#            self.width = self.width - loffset  # chop off offset amount
#            self.origin = [other.origin[0], self.origin[1]]

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

# notify of progress
print("P60")
sys.stdout.flush()

HEIGHT = led_matrix.height()
WIDTH = led_matrix.width()

if WIDTH > 8:
    LEFT_EDGE = 3
    RIGHT_EDGE = 12
else:
    LEFT_EDGE = -1
    RIGHT_EDGE = WIDTH

# initialize variables
curr_state = State.IDLE  # current state used for state machine
blocks = []              # current block elements on screen
start_width = 3           # pixel width of block on start
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
    if channel in [START, SELECT]:
        curr_state = State.EXIT
        return
    
    # else the button must be A
    if curr_state == State.PLAYING:
        # stop the block
        blocks[-1].stop()
        
        # check if block is touching previous block and crop
        if len(blocks) > 1:
            top_block = blocks[-1]
            base_block = blocks[-2]
            if top_block.adjacent(base_block):
                # crop block only if it hangs off the edge
#                if (top_block.origin[0] + top_block.width - 1) > (base_block.origin[0] + base_block.width - 1):
                top_block.crop(base_block)
                    
                # if hit the ceiling, display win screen 
                if len(blocks) == HEIGHT:
                    curr_state = State.WIN
                    return
            else:
                # top block was not touching base block, so we lose
                curr_state = State.LOSE
                return
        
        # create new block
        if len(blocks) % change_level == 0:  # check if to up difficulty
            if curr_width > 1:
                curr_width -= 1
            curr_speed += 8  # update current speed
        curr_width = min(blocks[-1].width, curr_width)
        blocks.append(Block([LEFT_EDGE+1, blocks[-1].origin[1]+1], curr_width))
        
    elif curr_state in [State.IDLE, State.WIN, State.LOSE]:
        # set up game
        blocks = [Block([LEFT_EDGE+1,0], start_width)]  # set up first block
        curr_width = start_width
        curr_speed = start_speed
        led_matrix.erase()
        draw_blocks()
        led_matrix.show()
        curr_state = State.PLAYING

GPIO.setmode(GPIO.BCM)
for but in [A, START, SELECT]:
    GPIO.setup(but, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(but, GPIO.FALLING, callback=button_handler, bouncetime=50)

# notify of progress
print("P70")
sys.stdout.flush()

title = led_matrix.LEDText("STACK-EM", font_name="large")

# notify of progress
print("P80")
sys.stdout.flush()

   
# create intro title (a vertical display of "STACKEM")
title = led_matrix.LEDText("M").rotate(90)
for character in reversed("STACKE"):
    # append a 1 pixel wide (high) spacing
    title.append(led_matrix.LEDSprite(width=1, height=title.height))
    # append next character
    title.append(led_matrix.LEDText(character).rotate(90))
# rotate title up
title.rotate(-90)   

# notify of progress
print("P100")
sys.stdout.flush()
        
# State Machine ==================

# notify menu we are ready for the led matrix
print("READY")
sys.stdout.flush()

while True:
    if curr_state == State.IDLE:
        # display scrolling virtical text
        y_pos = - title.height
        while y_pos < led_matrix.height():
            # if state changes stop scrolling and go to that state
            if curr_state != State.IDLE:
                break
            # display title in the center of the screen
            led_matrix.erase()
            led_matrix.sprite(title, (int(led_matrix.width()/2) - int(title.width/2), y_pos))
            led_matrix.show()
            y_pos += 1
            time.sleep(.1)
        

    elif curr_state == State.PLAYING:
        # show the blocks
        led_matrix.erase()
        draw_blocks()
        # draw edge lines if not whole screen
        if LEFT_EDGE != 0:
            led_matrix.line((LEFT_EDGE, 0), (LEFT_EDGE, HEIGHT-1))
        if RIGHT_EDGE != WIDTH:
            led_matrix.line((RIGHT_EDGE, 0), (RIGHT_EDGE, HEIGHT-1))
        
        led_matrix.show()
        time.sleep(1.0/curr_speed)
    
#            global button_pressed
        if blocks[-1].moving:
            # change direction if hit edge of screen
            if curr_direction == Direction.RIGHT:
                if blocks[-1].origin[0] + blocks[-1].width == RIGHT_EDGE:
                    curr_direction = Direction.LEFT
            elif blocks[-1].origin[0] == LEFT_EDGE+1:
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
        # draw edge lines if not whole screen
        if LEFT_EDGE != 0:
            led_matrix.line((LEFT_EDGE, 0), (LEFT_EDGE, HEIGHT-1))
        if RIGHT_EDGE != WIDTH:
            led_matrix.line((RIGHT_EDGE, 0), (RIGHT_EDGE, HEIGHT-1))
        led_matrix.show()
        time.sleep(.2)
        led_matrix.erase()
        blocks[-1].color = 0xF
        draw_blocks()
        # draw edge lines if not whole screen
        if LEFT_EDGE != 0:
            led_matrix.line((LEFT_EDGE, 0), (LEFT_EDGE, HEIGHT-1))
        if RIGHT_EDGE != WIDTH:
            led_matrix.line((RIGHT_EDGE, 0), (RIGHT_EDGE, HEIGHT-1))
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
    
    


