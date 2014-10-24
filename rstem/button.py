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

from rstem import gpio


PRESSED = gpio.FALLING
RELEASED = gpio.RISING
BOTH = gpio.BOTH

A = 4
B = 17
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
START = 27
SELECT = 22


class Button(object):
    """ A button from a GPIO port"""

    def __init__(self, port):
        """
        @param port: GPIO number (BCM mode) that button is plugged into
        @type port: int
        """
        self.port = port
        self.gpio = gpio.Pin(port)
        self.gpio.configure(gpio.INPUT)

    def is_pressed(self):
        """@returns: True if button is pressed"""
        return not bool(self.gpio.get_level())

    def was_clicked(self):
        return self.gpio.was_clicked()

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
        Button._verify_change_value(change)
        self.gpio.edge_detect(change, event_callback, bouncetime)

    def remove_call_on_change(self):
        """Removes the callback function set for this button.
        Does nothing if no callback function is set
        """
        self.gpio.remove_edge_detect()

    def wait_for_change(self, change=PRESSED):
        """Blocks until given change event happens

        @param change: type of event to watch for (either button.PRESSED, button.RELEASED, or button.BOTH)
        """
        Button._verify_change_value(change)
        self.gpio.wait_for_edge(change)
