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

from rstem import led_matrix
import RPi.GPIO as GPIO
import subprocess
import os
import sys
import time
import fcntl

# button ports
A = 4
B = 17
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
START = 27
SELECT = 22


# states
IN_MENU = 1
IN_GAME = 2
KONAMI = 3
curr_state = IN_MENU

konami_number = 0
konami_code = [UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT, RIGHT, B, A]

loading_text = led_matrix.LEDText("LOADING")

class Menu(object):

    HOLD_CLOCK_TIME = -15 # number of cycles to hold scrolling text
    
    def __init__(self, menu_items, show_loading=False):
        items = []
        # convert titles
        for i, item in enumerate(menu_items):
            if show_loading:
                led_matrix.erase()
                led_matrix.text(str(len(menu_items) - i))
                led_matrix.show()
            f = os.path.join(os.path.dirname(os.path.abspath(__file__)), item[1])
            if not os.path.isfile(f):
                raise IOError("File '" + f + "' could not be found.")
            items.append({
                "title": item[0], 
                "file": f,
                "text": led_matrix.LEDText(item[0], font_name="large")
                })
        self.items = items
        self.scrolling_text_pos = 0
        self.scrolling_text_clock = Menu.HOLD_CLOCK_TIME  # clock used to slow down scrolling text
        self.scrolling_text_cycle = 5  # number of cycles between scrolling tick
        
    def draw(self):
        # display menu items
        pos_y = 0
        selected_item = self.selected_item()
        
        # display all other items regularly
        for item in self.items:
            if pos_y >= led_matrix.height(): # don't diplay items outside of display
                break
            if item["title"] == selected_item["title"]:
                # display selected text scrolling
                x = self.scrolling_text_pos
                led_matrix.sprite(selected_item["text"], (x, pos_y))
                if self.scrolling_text_clock == self.scrolling_text_cycle:
                    self.scrolling_text_clock = 0
                    if self.scrolling_text_pos < -selected_item["text"].width:
                        self.scrolling_text_pos = led_matrix.width() - 1
                    else:
                        self.scrolling_text_pos -= 1
                self.scrolling_text_clock += 1
            else:
                led_matrix.sprite(item["text"], (0, pos_y))
            pos_y += item["text"].height + 1
    
    def _rotate(self, n):
        """Rotates counterclockwise if positive, clockwise if negative"""
        l = self.items
        self.items = l[n:] + l[:n]
    
    def scroll_down(self):
        self._rotate(1)
        self.scrolling_text_pos = 0
        self.scrolling_text_clock = Menu.HOLD_CLOCK_TIME
        
    def scroll_up(self):
        self._rotate(-1)
        self.scrolling_text_pos = 0
        self.scrolling_text_clock = Menu.HOLD_CLOCK_TIME
    
    def selected_item(self):
        """Returns selected item, which should be first inverted item."""
        return self.items[0]
                
    def run_selected_item(self):
        # start child process
        selected = self.selected_item()
        GPIO_cleanup()
        proc = subprocess.Popen([sys.executable, selected["file"]], stdout=subprocess.PIPE, close_fds=False)
        
        # make proc.stdout a non-blocking file
        fd = proc.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        finished = False
        print("starting up")
        # display loading screen until child process wants the led matrix
        while not proc.poll() and not finished:
            x_pos = led_matrix.width()
            y_pos = int(led_matrix.height()/2) - int(loading_text.height/2)
            while x_pos >= -loading_text.width:
                led_matrix.erase()
                led_matrix.sprite(loading_text, (x_pos, y_pos))
                led_matrix.show()
                x_pos -= 1

                # read stdout of the game process
                try: 
                    data = proc.stdout.readline()
                except:
                    data = False
                if data:
                    print(data)
                    
                # check if child process is ready to take control of matrix
                if data and data.decode("utf-8") == "READY\n":
                    finished = True
                    break
                time.sleep(0.05)
                
        print("wait for game to die")

        led_matrix.erase()  # clear the display
        led_matrix.show()
        # TODO: find out if we need to clean up led matrix too
        # wait till child process finishes
        proc.wait()
        GPIO_setup() # resetup GPIO
        
        
def button_handler(channel):
    global konami_number
    global curr_state
    if channel == konami_code[konami_number]:
        konami_number += 1  # continue progress towards konami code
        if konami_number == len(konami_code):  # konami code complete
            curr_state = KONAMI
            konami_number = 0
            return
    else:
        konami_number = 0  # reset progress, wrong button pressed
    if curr_state != KONAMI:
        if channel == A and konami_number == 0:
            curr_state = IN_GAME
        elif channel == UP:
            menu.scroll_up()
        elif channel == DOWN:
            menu.scroll_down()

def GPIO_setup():
    GPIO.setmode(GPIO.BCM)
    for button in [A, UP, DOWN, LEFT, RIGHT, B, START, SELECT]:
        GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(button, GPIO.FALLING, callback=button_handler, bouncetime=150)
        
def GPIO_cleanup():
    for button in [A, UP, DOWN, LEFT, RIGHT, B, START, SELECT]:
        GPIO.remove_event_detect(button)
    GPIO.cleanup()
    
    
# set up led matrix
led_matrix.init_matrices([(0,0),(8,0),(8,8),(0,8)], math_coords=False)
GPIO_setup()    
    
# set up menu
menu_items = [
    ["ASPIRIN", "aspirin.py"],
    ["CLOCK", "clock.py"],
    ["DICE", "dice.py"],
    ["PROTECTOR", "protector.py"],
    ["BREAKOUT", "breakout.py"],
    ["TETRIS", "tetris.py"],
    ["STACK-EM", "stackem.py"],
    ["SPACE INVADERS", "space_invaders.py"],
    ["FLAPPYBIRD", "flappybird.py"],
    ["GAME OF LIFE", "game_of_life.py"],
    ["SNAKE", "snake.py"]
]
menu_items.sort() # put in alphabetical order by titles
menu = Menu(menu_items, show_loading=True)




while True:
    if curr_state == IN_MENU:
        led_matrix.erase()
        menu.draw()
        led_matrix.show()
        time.sleep(0.01)
    elif curr_state == IN_GAME:
        menu.run_selected_item()  # run game and wait for it to die
        curr_state = IN_MENU
    elif curr_state == KONAMI:
        from random import shuffle, randint
        words = ["Brian", "Jason", "Jon", "Joe", "Steph", "Jed", "Tess"]
        shuffle(words)
        raspberrySTEM = "RaspberrySTEM"
        for name in words:
            sprite = led_matrix.LEDText(name, font_name="large")
            y_pos = randint(0,led_matrix.height()-sprite.height)
            x_pos = led_matrix.width()
            while x_pos >= -sprite.width:
                led_matrix.erase()
                led_matrix.sprite(sprite, (x_pos, y_pos))
                led_matrix.show()
                x_pos -= 1
                time.sleep(.05)
        
        logo = led_matrix.LEDText(raspberrySTEM, font_name="large")
        y_pos = int(led_matrix.height()/2) - int(logo.height/2)
        x_pos = led_matrix.width()
        while x_pos >= -logo.width:
            led_matrix.erase()
            led_matrix.sprite(logo, (x_pos, y_pos))
            led_matrix.show()
            x_pos -= 1
            time.sleep(0.05)
        curr_state = IN_MENU
        
    
