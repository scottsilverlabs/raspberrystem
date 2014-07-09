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
    
class Block(object):
    def __init__(self, origin, width, color=0xF):
        self.origin = origin
        self.width = width
        self.color = color
        
    def draw(self):
        """Draws block on led matrix display"""
        x_start, y_start = self.origin
        for x_offset in range(self.width):
            led2.point(x_start + x_offset, y_start, self.color)
            
    def stop(self):
        """Stops the block from moving"""
        pass

try:
    # SETUP ==========================

    # initialize variables
    curr_state = State.IDLE  # current state used for state machine
    blocks = []              # current block elements on screen

    # setup gpio buttons
    BUTTON=2  # GPIO pin button is connected to
    def button_handler(channel):
        if channel == BUTTON:
            if curr_state == State.PLAYING:
                blocks[-1].stop()  # stop the current moving block
                if blocks[-2]
            elif curr_state in [State.IDLE, State.WIN, State.LOSE]:
                # set up game
                blocks = []  # reset blocks
                draw_blocks()
                led2.show()
                curr_state = State.PLAYING

    GPIO.setmode(GPIO.BCM)
    GPIO.add_event_detect(BUTTON, GPIO.FALLING, callback=button_handler, bouncetime=100)
    
    # setup led matrix
    led2.init_grid(2,1,180)
    HEIGHT = led2.height()
    WIDTH = led2.width()

    def draw_blocks():
        """Draws the current blocks on screen"""
        led2.erase()
        for block in blocks:
            block.draw()
            
    # State Machine ==================
    
    while curr_state != State.DONE:
        if curr_state == State.IDLE:
            # TODO: do something cool
            pass
        elif curr_state == State.PLAYING:
            pass
        elif curr_state == State.WIN:
            pass
        elif curr_state == State.LOSE:
            pass
        else:
            raise RuntimeError("Invalid State")
        
    
    
    
    
    
    
    
    
    


