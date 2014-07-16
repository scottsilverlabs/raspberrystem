import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

FALLING = GPIO.FALLING
RISING = GPIO.RISING
BOTH = GPIO.BOTH

def cleanup():
    GPIO.cleanup()

class Button(object):

    def __init__(self, port, pressed_is_high=True):
        if pressed_is_high:
            pull_up_down = GPIO.PUD_DOWN
        else:
            pull_up_down = GPIO.PUD_UP
        self.port = port
        self.pressed_is_high = pressed_is_high
        GPIO.setup(port, GPIO.IN, pull_up_down=pull_up_down)
        
    def is_pressed(self):
        if self.pressed_is_high:
            return GPIO.input(self.port)
        else:
            return (not GPIO.input(self.port))
        
    def call_when_pressed(self, event_callback, bouncetime=200):
        GPIO.add_event_callback(self.port, callback=event_callback, bouncetime=bouncetime)
        
    def wait_for_edge(self, edge):
        if edge not in [FALLING, RISING, BOTH]:
            raise ValueError("Invalid edge")
        GPIO.wait_for_edge(self.port, edge)
