
from rstem import led_matrix, accel
import RPi.GPIO as GPIO
import time
import os
import sys
import random


# set up dice sprites
dice = {}
for value in range(1,7):
    dice[value] = led_matrix.LEDSprite(os.path.abspath(str(value) + ".spr"))
    
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

# TODO: make it work with more than one matrices
die = random.choice(dice.values())

while True:
    # exit if start button is pressed
    if GPIO.input(START) == 0:
        led_matrix.cleanup()
        GPIO.cleanup()
        sys.exit(0)
    
    # roll dice if A button is pressed
    if GPIO.input(A) == 0:
        # TODO: make a rolling dice animation
        die = random.choice(dice.values())
        
    
