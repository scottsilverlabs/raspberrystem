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
from threading import Thread, Event
from queue import Queue, Empty
import time
from rstem.gpio import Pin

class Button(Pin):
    """ A button from a GPIO port"""

    A = 4
    """GPIO number of the 'A' button on the GAMER keypad"""

    B = 17
    UP = 25
    DOWN = 24
    LEFT = 23
    RIGHT = 18
    START = 27
    SELECT = 22

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

    def is_pressed(self, press=True):
        pressed = not bool(self._get()) 
        return pressed if press else not pressed

    def is_released(self):
        return not self.is_pressed()

    def presses(self, press=True):
        _releases, _presses = self._edges()
        return _presses if press else _releases

    def one_press(self, press=True):
        return self._one_edge(0 if press else 1)

    def wait(self, press=True, timeout=None):
        return self._wait(0 if press else 1, timeout=timeout)

    @classmethod
    def wait_many(cls, buttons, press=True, timeout=None):
        # Python does not provide a way to wait on multiple Queues.  Big bummer.
        # To avoid overcomplicating this, we'll simply poll the queues.
        start = time.time()
        while timeout == None or timeout - (time.time() - start) < 0:
            for i, button in enumerate(buttons):
                button_found = button.wait(press=press, timeout=0)
                if button_found:
                    return i
        return None

    """ TBD:
    def callback(self): callback if press, release, or either
    """

__all__ = ['Button']
