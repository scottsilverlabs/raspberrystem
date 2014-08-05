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
#This is the third project in the "Space invaders" series.
#This project adds enemies

#Imports, need sys for exit function
from rstem import led_matrix
from rstem import accel
import RPi.GPIO as GPIO
import time

#Initialize matrix, accelerometer, and GPIO, the matrix layout and accelerometer channel may changes from user to user
led_matrix.init_grid(2)
accel.init(1)
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down = GPIO.PUD_UP)

#Game entity data
player_pos = [7, 0]
missles = []
enemies = []

#Game timing data, missles get updated and therefore move roughly sixty times faster than enemies initialy
game_tick = 0
game_tick_max = 64
enemy_tick = 60
start_time = time.time()

#Function to add missle at the players position to set of current missles
def fire_missle(channel):
    missles.append(Missle([int(round(player_pos[0])), int(round(player_pos[1]))],[0, 1]))

#Call fire_missle when fire button is pressed
GPIO.add_event_detect(4, GPIO.FALLING, callback=fire_missle, bouncetime = 300)

#Useful clamp function to make sure the data passed to point is on the matrix
def clamp(x):
    return max(0, min(x, 15))

#Missle keeps track of its current position and current direction
class Missle:
    
    def __init__(self, position, direction):
        self.pos = position
        self.dir = direction

#   Move missle on missle update tick
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
#       If it hits a wall move down two and change direction
        if self.pos[0] > 15:
            self.pos = [15, self.pos[1]-2]
            self.dir = [-1, 0]
        elif self.pos[0] < 0:
            self.pos = [0, self.pos[1]-2]
            self.dir = [1, 0]

#Setup initial enemies
for i in range(5):
    enemies.append(Enemy([i*3, 15], [1, 0]))
for i in range(5):
    enemies.append(Enemy([15-i*3 , 13], [-1, 0]))

try:
#   Start game
    while True:

#       Clear previous framebuffer    
        led_matrix.fill(0)

#       Redraw enemies and update if its their game tick
        for e in enemies:
            if game_tick%enemy_tick == 0 and not game_tick == 0:
                e.update()
            led_matrix.point(e.pos[0], e.pos[1])

#       Update and redraw missles
        for m in missles:
            m.update()    
            led_matrix.point(m.pos[0], m.pos[1])

#       Check for collisions
        for m in missles:
            for e in enemies:
                if m.pos == e.pos:
                    enemies.remove(e)
                    missles.remove(m)
#       Get angles from accelerometer
        data = accel.angles()

#       Generate smooth movement data using IIR filter, and make a 1/4 turn move
#       the player to the edge of the screen
        player_pos[0] = player_pos[0] + (clamp(data[0]*8*4/90 + 7) - player_pos[0])*0.1
        
#       Draw player
        led_matrix.point(int(round(player_pos[0])), int(round(player_pos[1])))

#       Show framebuffer
        led_matrix.show()

#       Delay one game tick, in this case 1ms
        time.sleep(0.001)

#       Make enemies speed up when their are less of them
        enemy_tick = int(len(enemies)*3)

#       Update game tick and wrap around
        game_tick = (game_tick+1)&(game_tick_max-1)

#Stop if player hits Ctrl-C
except KeyboardInterrupt:
        pass

#Clean everything up
finally:
        GPIO.cleanup()
        led_matrix.cleanup()