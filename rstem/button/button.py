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

    def __init__(self, port):
        self.port = port
        GPIO.setup(port, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
    def is_pressed(self):
        if GPIO.input(self.port):
            return False
        else:
            return True
        
    def call_when_pressed(self, event_callback, bouncetime=300):
        GPIO.add_event_detect(self.port, GPIO.FALLING, callback=event_callback, bouncetime=bouncetime)
        
    def wait_for_edge(self, edge):
        if edge not in [FALLING, RISING, BOTH]:
            raise ValueError("Invalid edge")
        GPIO.wait_for_edge(self.port, edge)
