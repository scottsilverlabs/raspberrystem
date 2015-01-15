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

active_pins = {}

class Pin:
    _ARG_PULL_DISABLE = 0
    _ARG_PULL_DOWN = 1
    _ARG_PULL_UP = 2

    def __init__(self, pin):
        self.gpio_dir = "/sys/class/gpio/gpio%d" % pin
        self.pin = pin
        if pin in PINS:
            if not os.path.exists(self.gpio_dir):
                with open("/sys/class/gpio/export", "w") as f:
                    f.write("%d\n" % pin)
        else:
            raise ValueError("Invalid GPIO pin")

        global active_pins
        if pin in active_pins:
            active_pins[pin]._deactivate()
        active_pins[pin] = self

    def _pullup(self, pin, enable):
        os.system("pullup.sbin %d %d" % (pin, enable))

    def _enable_pullup(self, pin):
        self._pullup(pin, self._ARG_PULL_UP)

    def _disable_pullup(self, pin):
        self._pullup(pin, self._ARG_PULL_DISABLE)

    def _enable_pulldown(self, pin):
        self._pullup(pin, self._ARG_PULL_DOWN)

    def _disable_pulldown(self, pin):
        self._pullup(pin, self._ARG_PULL_DISABLE)

    def _deactivate(self):
        del active_pins[self.pin]


class Output(Pin):
    def __init__(self, pin, active_low=False):
        super().__init__(pin)
        self._active_low = active_low
        with open(self.gpio_dir + "/direction", "w") as fdirection:
            fdirection.write("out")
            self._fvalue = open(self.gpio_dir + "/value", "w")

    def _set(self, level):
        self._fvalue.seek(0)
        self._fvalue.write('1' if level else '0')
        self._fvalue.flush()

    def on(self):
        self._set(not self._active_low)

    def off(self):
        self._set(self._active_low)

class Button(Pin):
    PRESS = 1
    RELEASE = 2
    BOTH = 3

    def __init__(self, pin):
        """Hey dude

        **test** *itails*
        This is `self`.

        `pin`

        `is_pressed`


        `is_pressed()`

        `Button.is_pressed()`

        `gpio.Button.is_pressed()`

        `rstem.gpio.Button.is_pressed()`

        `is_pressed`

        `Button.is_pressed`

        `gpio.Button.is_pressed`

        `rstem.gpio.Button.is_pressed`

        """

        super().__init__(pin)

        with open(self.gpio_dir + "/direction", "w") as fdirection:
            fdirection.write("in")

        self._enable_pullup(self.pin)

        self._fvalue = open(self.gpio_dir + "/value", "r")

        self._button_queue = Queue()
        self._poll_thread_stop = Event()
        self._poll_thread = Thread(target=self.__button_poll_thread, args=())
        self._poll_thread.daemon = True
        self._poll_thread.start()

    def __button_poll_thread(self):
        """Run function used in self._poll_thread"""
        previous = -1

        bounce_time = 0.030
        while not self._poll_thread_stop.wait(bounce_time):
            self._fvalue.seek(0)
            read = self._fvalue.read().strip()
            if len(read):
                current = 1 if read == '1' else 0
                if previous >= 0 and current != previous:
                    self._button_queue.put(current)
                previous = current

    def _edges(self):
        try:
            releases, presses = 0, 0
            while True:
                level = self._button_queue.get_nowait()
                if level:
                    releases += 1
                else:
                    presses += 1
        except Empty:
            pass
        return releases, presses

    def _one_edge(self, level_wanted):
        try:
            while True:
                level = self._button_queue.get_nowait()
                if level == level_wanted:
                    return 1
        except Empty:
            pass
        return 0

    def _wait(self, level_wanted, timeout=None):
        try:
            start = time.time()
            while True:
                if timeout != None:
                    remaining = max(0, timeout - (time.time() - start))
                    level = self._button_queue.get(timeout=remaining)
                else:
                    level = self._button_queue.get()
                if level == level_wanted:
                    return True
        except Empty:
            return False

    def _get(self):
        self._fvalue.seek(0)
        return int(self._fvalue.read())

    def _deactivate(self):
        if self._poll_thread:
            self._poll_thread_stop.set()
            self._poll_thread.join()
        super()._deactivate()

    def is_pressed(self, change=PRESS):
        pressed = not bool(self._get()) 
        return pressed if change == self.PRESS else not pressed

    def is_released(self):
        return not self.is_pressed()

    def presses(self, change=PRESS):
        _releases, _presses = self._edges()
        return _presses if change == self.PRESS else _releases

    def one_press(self, change=PRESS):
        return self._one_edge(0 if change == self.PRESS else 1)

    def wait(self, change=PRESS, timeout=None):
        return self._wait(0 if change == self.PRESS else 1, timeout=timeout)

    @classmethod
    def wait_many(cls, buttons, change=PRESS, timeout=None):
        # Python does not provide a way to wait on multiple Queues.  Big bummer.
        # To avoid overcomplicating this, we'll simply poll the queues.
        start = time.time()
        while timeout == None or timeout - (time.time() - start) < 0:
            for i, button in enumerate(buttons):
                button_found = button.wait(change=change, timeout=0)
                if button_found:
                    return i
        return None

    """ TBD:
    def callback(self): callback if press, release, or either
    """

class DisablePin(Pin):
    def _deactivate(self):
        with open(self.gpio_dir + "/direction", "w") as fdirection:
            fdirection.write("in")
        super()._deactivate()

__all__ = ['Button', 'Output', 'DisablePin']

