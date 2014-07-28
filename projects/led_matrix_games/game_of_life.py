import sys
import os
from rstem import led_matrix
import RPi.GPIO as GPIO

def next_gen(curr_gen):
    pass
    

class State(object):
    START, IN_GAME, EXIT = range(3)
    
curr_state = State.START

# setup exit button
EXIT = 18
def button_handler(channel):
    global curr_state
    if channel == EXIT:
        curr_state = State.EXIT
GPIO.setmode(GPIO.BCM)
GPIO.setup(EXIT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(EXIT, GPIO.FALLING, callback=button_handler, bouncetime=300)
    
while True:
    if curr_state == State.IN_GAME:
        pass
    elif curr_state == State.START:
        pass
    elif curr_state == State.EXIT:
        pass
    else:
        raise ValueError("Invalid state")
