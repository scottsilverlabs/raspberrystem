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

from rstem import led_matrix, accel
import RPi.GPIO as GPIO
import time
import os
import sys
import random


# set up led matrix
#led_matrix.init_grid(2,2)
led_matrix.init_matrices([(0,8),(8,8),(8,0),(0,0)])


# set up accelerometer
accel.init(1)

# set up GPIO
GPIO.setmode(GPIO.BCM)

# set up dice sprites
dice = []
for value in range(1,7):
    sprite = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dice_sprites", str(value) + ".spr")
    dice.append(led_matrix.LEDSprite(sprite))
    
# set up buttons
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
A = 4
B = 17
START = 27
SELECT = 22

# setup start button to exit game
GPIO.setup(START, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# setup A button to roll dice
GPIO.setup(A, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# create flag to indicate to display some dice initially on start up
just_started = True

# get base_elevation
base_elevation = accel.angles()[2]

# set change in angle/acceleration needed to roll dice
THRESHOLD = 20

while True:
    # exit if start button is pressed
    if GPIO.input(START) == 0:
        led_matrix.cleanup()
        GPIO.cleanup()
        sys.exit(0)
    
    # roll dice if A button is pressed or accelerometer detects steep enough angle
    if just_started or GPIO.input(A) == 0 or abs(accel.angles()[2] - base_elevation) > THRESHOLD:
        led_matrix.erase()  # clear old dice values
        # set a new random die at each matrix
        for y in range(0, led_matrix.height(), 8):
            for x in range(0, led_matrix.width(), 8):
                led_matrix.sprite(random.choice(dice), (x+1,y+1))
        led_matrix.show()
        just_started = False

