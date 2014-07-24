import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

PRESSED = GPIO.FALLING
RELEASED = GPIO.RISING
BOTH = GPIO.BOTH

def cleanup():
    GPIO.cleanup()

class Button(object):

    def __init__(self, port):
        self.port = port
        GPIO.setup(port, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
    def is_pressed(self):
        return not bool(GPIO.input(self.port)):

    def _verify_change_value(change):
        if change not in [PRESSED, RELEASED, BOTH]:
            raise ValueError("Invalid change")
        
    def call_on_change(self, event_callback, change=PRESSED, bouncetime=300):
        _verify_change_value(change)
        GPIO.add_event_detect(self.port, change, callback=event_callback, bouncetime=bouncetime)
        
    def wait_for_change(self, change):
        _verify_change_value(change)
        GPIO.wait_for_edge(self.port, change)
