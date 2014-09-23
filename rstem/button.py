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

import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# variables that can be used by user programs
PRESSED = GPIO.FALLING
RELEASED = GPIO.RISING
BOTH = GPIO.BOTH


def cleanup():
    """Cleans up the GPIO port"""
    GPIO.cleanup()

class Button(object):
    """ A button from a GPIO port"""
    def __init__(self, port):
        """
        @param port: GPIO number (BCM mode) that button is plugged into
        @type port: int
        """
        self.port = port
        GPIO.setup(port, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
    def is_pressed(self):
        """@returns: True if button is pressed"""
        return not bool(GPIO.input(self.port))

    def _verify_change_value(change):
        if change not in [PRESSED, RELEASED, BOTH]:
            raise ValueError("Invalid change")
        
    def call_on_change(self, event_callback, change=PRESSED, bouncetime=300):
        """Calls given event_callback function when button changes state (example pressed).
        
        @param event_callback: function to call when button changes state
        @type event_callback: function
        @param change: type of event to watch for (either button.PRESSED, button.RELEASED, or button.BOTH)
        @param bouncetime: msec to debounce button
        @type bouncetime: int8
        
        @warning: Function must have the first argument be the port number
        """
        _verify_change_value(change)
        GPIO.add_event_detect(self.port, change, callback=event_callback, bouncetime=bouncetime)
        
    def wait_for_change(self, change):
        """Blocks until given change event happens
        
        @param change: type of event to watch for (either button.PRESSED, button.RELEASED, or button.BOTH)
        """
        _verify_change_value(change)
        GPIO.wait_for_edge(self.port, change)

A_port = 4
B_port = 17
UP_port = 25
DOWN_port = 24
LEFT_port = 23
RIGHT_port = 18
START_port = 27
SELECT_port = 22


class A(Button):
    def __init__(self):
        super(A, self).__init__(A_port)

class B(Button):
    def __init__(self):
        super(B, self).__init__(B_port)

class UP(Button):
    def __init__(self):
        super(UP, self).__init__(UP_port)

class DOWN(Button):
    def __init__(self):
        super(DOWN, self).__init__(DOWN_port)

class LEFT(Button):
    def __init__(self):
        super(LEFT, self).__init__(LEFT_port)

class RIGHT(Button):
    def __init__(self):
        super(RIGHT, self).__init__(RIGHT_port)

class START(Button):
    def __init__(self):
        super(START, self).__init__(START_port)

class SELECT(Button):
    def __init__(self):
        super(SELECT, self).__init__(SELECT_port)
