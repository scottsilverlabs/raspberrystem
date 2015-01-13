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

PINS = [2, 3, 4, 14, 15, 17, 18, 22, 23, 24, 25, 27]

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
        self.edge = NONE
        self.last = 1
        self.mutex = Lock()
        self.poll_thread = None
        self.poll_thread_stop = None
        if pin in PINS:
            if not os.path.exists(self.gpio_dir):
                with open("/sys/class/gpio/export", "w") as f:
                    f.write("%d\n" % pin)

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

    def __poll_thread_run(self, callback, bouncetime):
        """Run function used in poll_thread"""
        # NOTE: self will not change once this is called
        po = select.epoll()
        po.register(self.fvalue, select.POLLIN | select.EPOLLPRI | select.EPOLLET)
        last_time = 0
        first_time = True  # used to ignore first trigger
        # TODO: ignore second trigger too if edge = rising/falling?

        while not self.poll_thread_stop.is_set():
            event = po.poll(1)
            if len(event) == 0:
                # timeout
                continue
            self.fvalue.seek(0)
            if not first_time:
                timenow = time.time()
                if (timenow - last_time) > (bouncetime/1000) or last_time == 0:
                    callback(self.pin)
                    last_time = timenow
            else:
                first_time = False

    def __set_edge(self, edge):
        with self.mutex:
            with open(self.gpio_dir + "/edge", "w") as fedge:
                self.edge = edge
                fedge.write(edge)

    def __end_thread(self):
        if self.poll_thread and self.poll_thread.isAlive():
            # self.poll_thread_running = False
            self.poll_thread_stop.set()

            while self.poll_thread.isAlive():
                self.poll_thread.join(1)

    def _remove_edge_detect(self):
        """Removes edge detect interrupt"""
        self.__set_edge(NONE)
        self.__end_thread()

    def _wait_for_edge(self, edge):
        """Blocks until the given edge has happened
        @param edge: Either gpio.FALLING, gpio.RISING, gpio.BOTH
        @type edge: string
        @throws: ValueError
        """
        if self.direction != INPUT:
            raise ValueError("GPIO must be configured to be an input first.")
        if edge not in [RISING, FALLING, BOTH]:
            raise ValueError("Invalid edge!")
        self.__set_edge(edge)

        # wait for edge
        po = select.epoll()
        po.register(self.fvalue, select.POLLIN | select.EPOLLPRI | select.EPOLLET)
        # last_time = 0
        first_time = True  # used to ignore first trigger

        while True:
            event = po.poll(60)
            if len(event) == 0:
                # timeout to see if edge has changed
                if self.edge == NONE:
                    break
                else:
                    continue
            self.fvalue.seek(0)
            if not first_time:
                break
            else:
                first_time = False

    def _edge_detect(self, edge, callback=None, bouncetime=200):
        """Sets up edge detection interrupt.
        @param edge: either gpio.NONE, gpio.RISING, gpio.FALLING, or gpio.BOTH
        @type edge: int
        @param callback: Function to call when given edge has been detected.
        @type callback: function
        @param bouncetime: Debounce time in milliseconds.
        @type bouncetime: int
        @note: First parameter of callback function will be the pin number of gpio that called it.
        """
        if self.direction != INPUT:
            raise ValueError("GPIO must be configured to be an input first.")
        if callback is None and edge != NONE:
            raise ValueError("Callback function must be given if edge is not NONE")
        if edge not in [NONE, RISING, FALLING, BOTH]:
            raise ValueError("Edge must be NONE, RISING, FALLING, or BOTH")

        self.__set_edge(edge)

        if edge != NONE:
            self.__end_thread()  # end any previous callback functions
            self.poll_thread_stop = Event()
            self.poll_thread = Thread(target=_Pin.__poll_thread_run, args=(self, callback, bouncetime))
            self.poll_thread.daemon = True
            self.poll_thread.start()


    def _configure(self, direction, pull=None):
        """Configure the GPIO pin to either be an input, output or disabled.
        @param direction: Either gpio.INPUT, gpio.OUTPUT, or gpio.DISABLED
        @type direction: int
        """
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
                elif direction == DISABLED:
                    fdirection.write("in")
                    self.fvalue.close()

    def _was_clicked(self):
        # TODO: make work for any type of edge change and rename function
        """Detects whether the GPIO has been clicked or on since the pin has been initialized or
        since the last time was_clicked() has been called.
        @returns: boolean
        """
        level = self.get_level()
        clicked = level == 1 and self.last == 0
        self.last = level
        return clicked

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


class Input(_Pin):
    def __init__(self, pin, active_low=False, pull=None):
        super().__init__(pin)
        self._active_low = active_low
        self._configure(INPUT, pull)

    def is_on(self):
        return bool(self.level) != self._active_low

    def is_off(self):
        return not self.is_on()

    level = _Pin._level

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
        return bool(self.level)

    def is_pressed(self):
        return not self.is_released()

    level = _Pin._level
