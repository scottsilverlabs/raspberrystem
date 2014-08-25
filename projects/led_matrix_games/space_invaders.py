
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
#Imports, need sys for exit function
#This project finishes the game and adds winning
#losing and scoring functions.
from rstem import led_matrix
from rstem import accel
import RPi.GPIO as GPIO
import time
import sys

#Initialize matrix, accelerometer, and GPIO, the matrix layout and accelerometer channel may changes from user to user
led_matrix.init_grid(2)
accel.init(1)
GPIO.setmode(GPIO.BCM)

#Game entity data
player_pos = [7, 0]
missles = []
enemies = []

#Game timing data, missles get updated and therefore move roughly sixty times faster than enemies initialy
game_tick = 0
game_tick_max = 64
enemy_tick = 60
start_time = time.time()

# Set up States for finite state machine
class State(object):
    PLAYING, IDLE, WIN, LOSE = range(4)
    
state == State.IDLE

#Function to add missle at the players position to set of current missles
def fire_missle(channel):
    missles.append(Missle([int(round(player_pos[0])), int(round(player_pos[1]))],[0, 1]))


def scroll_text(string):
    """Scrolls the given text"""
    msg = led_matrix.LEDText(string, font_name='large')
    # store state beforehand
    prev_state = state
    for i in range(len(string)*6 + 15):
        # exit if state has changed in the middle of scrolling
        if state != prev_state:
            return
        led_matrix.erase()
        led_matrix.text(msg, (15 - i, 7))
        led_matrix.show()
        time.sleep(0.1)


#Useful clamp function to make sure the data passed to point is on the matrix
def clamp(x):
    if(x > 15):
        x = 15
    if(x < 0):
        x = 0
    return x


#Missle keeps track of its current position and current direction
class Missle:
    
    def __init__(self, position, direction):
        self.pos = position
        self.dir = direction

#    Move missle on missle update tick
    def update(self):
        self.pos[0] = self.pos[0] + self.dir[0]
        self.pos[1] = self.pos[1] + self.dir[1]
        if self.pos[1] > 15 or self.pos[1] < 0 or self.pos[0] < 0 or self.pos[1] > 15:
            missles.remove(self)

#Enemy keeps track of its current position and direction
class Enemy:

    def __init__(self, position, direction):
        self.pos = position
        self.dir = direction
    
    def update(self):
        self.pos[0] = self.pos[0] + self.dir[0]
        self.pos[1] = self.pos[1] + self.dir[1]
#        If it hits a wall move down two and change direction
        if self.pos[0] > 15:
            self.pos = [15, self.pos[1]-2]
            self.dir = [-1, 0]
        elif self.pos[0] < 0:
            self.pos = [0, self.pos[1]-2]
            self.dir = [1, 0]
#        If an enemy makes it past the player call the lose function
        if self.pos[1] < 0:
            state = State.LOSE

# Setup buttons
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
SELECT = 22
START = 27
A = 4
B = 17

# what to do during a button press
def button_handler(button):
    global curr_state
    if button == START:
        state = State.EXIT
    elif state == State.PLAYING and button == A:
        fire_missle()
    elif state in [State.IDLE, State.WIN, State.LOSE] and button == A:
        # reset variables and then start the game
        player_pos = [7, 0]
        missles = []
        enemies = []
        #Setup initial enemies
        for i in range(5):
            enemies.append(Enemy([i*3, 15], [1, 0]))
        for i in range(5):
            enemies.append(Enemy([15-i*3 , 13], [-1, 0]))
        state = State.PLAYING

GPIO.setmode(GPIO.BCM)
for button in [A, START]:
    GPIO.setup(button, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.add_event_detect(button, GPIO.FALLING, callback=button_handler, bouncetime=300)
    

#	Start game
while True:
    if state == State.WIN:
        scroll_text("You Won in %is" % (int(time.time()-start_time)))
        
    elif state == State.LOSE:
        scroll_text("GAME OVER!")
        
    elif state == State.EXIT:
        led_matrix.cleanup()
        GPIO.cleanup()
        sys.exit(0)
        
    elif state == State.IDLE:
        scroll_text("SPACE INVADERS!!!")
        
    elif state == State.PLAYING:
#    	Clear previous framebuffer    
        led_matrix.fill(0)

#    	Player wins if no more enemies are left
        if len(enemies) == 0:
            state == State.WIN
            continue

#  		Redraw enemies and update if its their game tick
        for e in enemies:
            if game_tick%enemy_tick == 0 and not game_tick == 0:
                e.update()
            led_matrix.point(e.pos[0], e.pos[1])
        if state != State.PLAYING:
            continue

# 	    Update and redraw missles
        for m in missles:
            m.update()    
            led_matrix.point(m.pos[0], m.pos[1])

#   	Check for collisions
        for m in missles:
            for e in enemies:
                if m.pos == e.pos:
                    enemies.remove(e)
                    missles.remove(m)
#   	Get angles from accelerometer
        data = accel.angles()

#   	Generate smooth movement data using IIR filter, and make a 1/4 turn move
#   	the player to the edge of the screen
        player_pos[0] = player_pos[0] + (clamp(data[0]*8*4/90 + 7) - player_pos[0])*0.1
        
#	    Draw player
        led_matrix.point(int(round(player_pos[0])), int(round(player_pos[1])))

#    	Show framebuffer
        led_matrix.show()

#    	Delay one game tick, in this case 1ms
        time.sleep(0.001)

#   	 Make enemies speed up when their are less of them
        enemy_tick = int(len(enemies)*3)

#	    Update game tick and wrap around
        game_tick = (game_tick+1)&(game_tick_max-1)
