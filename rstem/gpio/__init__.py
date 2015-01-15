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

button_threads = {}

PRESS = 1
RELEASE = 2
BOTH = 3

class _Pin:
    _ARG_PULL_DISABLE = 0
    _ARG_PULL_DOWN = 1
    _ARG_PULL_UP = 2

    def __init__(self, pin):
        self.gpio_dir = "/sys/class/gpio/gpio%d" % pin
        self.pin = pin
        self.mutex = Lock()
        self.poll_thread = None
        self.poll_thread_stop = None
        self.fvalue = None
        if pin in PINS:
            if not os.path.exists(self.gpio_dir):
                with open("/sys/class/gpio/export", "w") as f:
                    f.write("%d\n" % pin)
        else:
            raise ValueError("Invalid GPIO pin")

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

    def _end_thread(self):
        global button_threads
        if self.pin in button_threads:
            poll_thread, poll_thread_stop = button_threads[self.pin]
            if poll_thread:
                poll_thread_stop.set()
                poll_thread.join()
            self.poll_thread = None
            del button_threads[self.pin]


class Output(_Pin):
    def __init__(self, pin, active_low=False):
        super().__init__(pin)
        self._active_low = active_low
        with open(self.gpio_dir + "/direction", "w") as fdirection:
            fdirection.write("out")
            self.fvalue = open(self.gpio_dir + "/value", "w")

    def _set(self, level):
        self.fvalue.seek(0)
        self.fvalue.write('1' if level else '0')
        self.fvalue.flush()

    def on(self):
        self._set(not self._active_low)

    def off(self):
        self._set(self._active_low)

class Button(_Pin):
    def __init__(self, pin):
        super().__init__(pin)

        global button_threads

        with open(self.gpio_dir + "/direction", "w") as fdirection:
            fdirection.write("in")

        self._enable_pullup(self.pin)

        self.fvalue = open(self.gpio_dir + "/value", "r")

        self._end_thread()  # end any previous callback functions

        self.button_queue = Queue()
        self.poll_thread_stop = Event()
        self.poll_thread = Thread(target=self.__button_poll_thread, args=())
        button_threads[self.pin] = self.poll_thread, self.poll_thread_stop
        self.poll_thread.daemon = True
        self.poll_thread.start()

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

    def _one_edge(self, level_wanted):
        try:
            while True:
                level = self.button_queue.get_nowait()
                if level == level_wanted:
                    return 1
        except Empty:
            pass
        return 0

    def _wait(self, level_wanted, timeout=None):
        try:
            start = time.time()
            while True:
                if timeout:
                    remaining = max(0, time.time() + timeout - start)
                    level = self.button_queue.get(timeout=remaining)
                else:
                    level = self.button_queue.get()
                if level == level_wanted:
                    return True
        except Empty:
            return False

    def _get(self):
        self.fvalue.seek(0)
        return int(self.fvalue.read())

    def is_pressed(self, change=PRESS):
        pressed = not bool(self._get()) 
        return pressed if change == PRESS else not pressed

    def is_released(self):
        return not self.is_pressed()

    def presses(self, change=PRESS):
        _releases, _presses = self._edges()
        return _presses if change == PRESS else _releases

    def one_press(self, change=PRESS):
        return self._one_edge(0 if change == PRESS else 1)

    def wait(self, change=PRESS, timeout=None):
        return self._wait(0 if change == PRESS else 1, timeout=timeout)

    """ TBD:
    def callback(self): callback if press, release, or either
    classmethod versions of the above, that can take a list of buttons
    """

class DisabledPin(_Pin):
    def __init__(self, pin):
        super().__init__(pin)
        with open(self.gpio_dir + "/direction", "w") as fdirection:
            self._end_thread()  # end any previous callback functions
            fdirection.write("in")
