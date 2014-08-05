
from rstem import led_matrix, accel
import RPi.GPIO as GPIO
import time
import os
import sys
import random


# set up led matrix
led_matrix.init_grid()

# set up dice sprites
dice = []
for value in range(1,7):
    dice.append(led_matrix.LEDSprite(os.path.abspath(str(value) + ".spr")))
    
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
GPIO.setmode(GPIO.BCM)
GPIO.setup(START, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# setup A button to roll dice
GPIO.setup(A, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# create flag to indicate to display initially on start up
just_started = True

while True:
    # exit if start button is pressed
    if GPIO.input(START) == 0:
        led_matrix.cleanup()
        GPIO.cleanup()
        sys.exit(0)
    
    # roll dice if A button is pressed
    if GPIO.input(A) == 0 or just_started:
        led_matrix.erase()  # clear old dice values
        for y in range(0, led_matrix.height(), 8):
            for x in range(0, led_matrix.width(), 8):
                led_matrix.sprite(random.choice(dice), (x+1,y+1))
        led_matrix.show()
        just_started = False

