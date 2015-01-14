#!/usr/bin/env python3
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
import select
import time
from threading import Thread, Lock, Event
from queue import Queue, Empty

PINS = [2, 3, 4, 14, 15, 17, 18, 22, 23, 24, 25, 27]

input_threads = {}

# Directions
OUTPUT = 1
INPUT = 2
DISABLED = 3

PULL_UP = "pull_up"
PULL_DOWN = "pull_down"

# Edge Detection
NONE = "none"
RISING = "rising"
FALLING = "falling"
BOTH = "both"

ARG_PULL_DISABLE = 0
ARG_PULL_DOWN = 1
ARG_PULL_UP = 2

HIGH = 1
LOW = 0


class _Pin:
    def __init__(self, pin):
        self.gpio_dir = "/sys/class/gpio/gpio%d" % pin
        self.pin = pin
        self.direction = DISABLED
        self.mutex = Lock()
        self.poll_thread = None
        self.poll_thread_stop = None
        self.previous = 0
        self.rising = 0
        self.falling = 0
        self.fvalue = None
        if pin in PINS:
            if not os.path.exists(self.gpio_dir):
                with open("/sys/class/gpio/export", "w") as f:
                    f.write("%d\n" % pin)
        else:
            raise ValueError("Invalid GPIO pin")

    def __pullup(self, pin, enable):
        os.system("pullup.sbin %d %d" % (pin, enable))

    def __enable_pullup(self, pin):
        self.__pullup(pin, ARG_PULL_UP)

    def __disable_pullup(self, pin):
        self.__pullup(pin, ARG_PULL_DISABLE)

    def __enable_pulldown(self, pin):
        self.__pullup(pin, ARG_PULL_DOWN)

    def __disable_pulldown(self, pin):
        self.__pullup(pin, ARG_PULL_DISABLE)

    def __button_poll_thread(self):
        """Run function used in poll_thread"""
        previous = -1

        bounce_time = 0.030
        while not self.poll_thread_stop.wait(bounce_time):
            self.fvalue.seek(0)
            read = self.fvalue.read().strip()
            if len(read):
                with self.mutex:
                    current = 1 if read == '1' else 0
                    if previous >= 0 and current != previous:
                        self.button_queue.put(current)
                    previous = current

    def _edges(self):
        try:
            releases, presses = 0, 0
            while True:
                level = self.button_queue.get_nowait()
                if level:
                    releases += 1
                else:
                    presses += 1
        except Empty:
            pass
        return releases, presses

    def __end_thread(self):
        global input_threads
        if self.pin in input_threads:
            poll_thread, poll_thread_stop = input_threads[self.pin]
            if poll_thread:
                poll_thread_stop.set()
                poll_thread.join()
            self.poll_thread = None
            del input_threads[self.pin]

    def _configure(self, direction, pull=None):
        """Configure the GPIO pin to either be an input, output or disabled.
        @param direction: Either gpio.INPUT, gpio.OUTPUT, or gpio.DISABLED
        @type direction: int
        """
        global input_threads

        if direction not in [INPUT, OUTPUT, DISABLED]:
            raise ValueError("Direction must be INPUT, OUTPUT or DISABLED")

        with self.mutex:
            with open(self.gpio_dir + "/direction", "w") as fdirection:
                self.direction = direction
                if direction == OUTPUT:
                    # For future use
                    fdirection.write("out")
                    self.fvalue = open(self.gpio_dir + "/value", "w")
                    if pull:
                        raise ValueError("Can't set pull resistor on output")
                elif direction == INPUT:
                    if pull:
                        self.__pullup(self.pin, ARG_PULL_UP if pull == PULL_UP else ARG_PULL_DOWN)
                    fdirection.write("in")
                    self.fvalue = open(self.gpio_dir + "/value", "r")
                    self.__end_thread()  # end any previous callback functions
                    self.button_queue = Queue()
                    self.poll_thread_stop = Event()
                    self.poll_thread = Thread(target=_Pin.__button_poll_thread, args=(self,))
                    input_threads[self.pin] = self.poll_thread, self.poll_thread_stop
                    self.poll_thread.daemon = True
                    self.poll_thread.start()
                elif direction == DISABLED:
                    self.__end_thread()  # end any previous callback functions
                    fdirection.write("in")
                    if self.fvalue:
                        self.fvalue.close()

    @property
    def _level(self):
        """Returns the current level of the GPIO pin.
        @returns: int (1 for HIGH, 0 for LOW)
        @note: The GPIO pins are active low.
        """
        if self.direction != INPUT:
            raise ValueError("GPIO must be configured to be an INPUT!")
        with self.mutex:
            self.fvalue.seek(0)
            return int(self.fvalue.read())

    @_level.setter
    def _level(self, level):
        """Sets the level of the GPIO port.
        @param level: Level to set. Must be either HIGH or LOW.
        @param level: int
        """
        if self.direction != OUTPUT:
            raise ValueError("GPIO must be configured to be an OUTPUT!")
        with self.mutex:
            self.fvalue.seek(0)
            self.fvalue.write('1' if level else '0')
            self.fvalue.flush()


class Output(_Pin):
    def __init__(self, pin, active_low=False):
        super().__init__(pin)
        self._active_low = active_low
        self._configure(OUTPUT)

    def on(self):
        self.level = not self._active_low

    def off(self):
        self.level = self._active_low

    level = _Pin._level

class Button(_Pin):
    def __init__(self, pin):
        super().__init__(pin)
        self._configure(INPUT, pull=PULL_UP)

    def is_released(self):
        return bool(self._level)

    def is_pressed(self):
        return not self.is_released()

    def presses(self):
        _releases, _presses = self._edges()
        return _presses

    def releases(self):
        _releases, _presses = self._edges()
        return _releases

    """ TBD:
    def one_press(self): like presses, but decrements the presses instead of reseting
    def one_release(self): like releases, but decrements the releases instead of reseting
    def wait(self): wait for press, release, or either
    def callback(self): callback if press, release, or either
    classmethod versions of the above, that can take a list of buttons
    """

class DisabledPin(_Pin):
    def __init__(self, pin):
        super().__init__(pin)
        self._configure(DISABLED)
