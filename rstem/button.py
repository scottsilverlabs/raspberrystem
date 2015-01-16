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
    """A button from a GPIO port.

    A `rstem.button.Button` configures a physical button hooked up to a GPIO
    pins.  The button should be connected from the GPIO pin to ground.

    `rstem.button.Button` provides a set of functions that make it easy to test
    if and when a button is pressed.  The `rstem.button.Button`
    object reads button presses in the background so that the calling program
    won't lose presses.  Presses and releases are kept in a queue so that the
    caller can get at any time.

    More details: The GPIO is configured with an internal pullup so that when
    the button NOT pressed, the GPIO input is high, but when the button is
    pressed, the input is low (shorted to ground).  Additionaly, The
    `rstem.button.Button` object handles button debouncing.
    """

    A = 4
    """GPIO number of the 'A' button on the GAMER keypad"""
    B = 17
    """GPIO number of the 'B' button on the GAMER keypad"""
    UP = 25
    """GPIO number of the 'UP' button on the GAMER keypad"""
    DOWN = 24
    """GPIO number of the 'DOWN' button on the GAMER keypad"""
    LEFT = 23
    """GPIO number of the 'LEFT' button on the GAMER keypad"""
    RIGHT = 18
    """GPIO number of the 'RIGHT' button on the GAMER keypad"""
    START = 27
    """GPIO number of the 'START' button on the GAMER keypad"""
    SELECT = 22
    """GPIO number of the 'SELECT' button on the GAMER keypad"""

    def __init__(self, pin):
        """Create a new `Button`

        `pin` is the number of the GPIO as labeled on the RaspberrySTEM
        connector.  It is the GPIO number of used by the Broadcom processor on
        the Raspberry Pi.
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
        """Reports if the button is pressed.

        Returns `True` if the button is pressed, otherwise False.  If `press`
        is `False`, then it does exactly the opposite - that is, it reports if
        the button released instead of pressed.
        """
        pressed = not bool(self._get())
        return pressed if press else not pressed

    def is_released(self):
        """Reports if the button is pressed.

        Equivalent to `not self.is_pressed()`.
        """
        return not self.is_pressed()

    def presses(self, press=True):
        """Returns the number of presses since this function was last called.

        Button presses and releases are queued up - this function reads all
        the presses/releases from the queue and returns the total number of
        presses.  Reading the full queue effectively resets the number of
        presses and releases to zero.

        Alternatively, if `press` is `False`, this function returns the number
        of releases since this function was last called.
        """
        _releases, _presses = self._edges()
        return _presses if press else _releases

    def one_press(self, press=True):
        """Reports if a single press has occured.

        Button presses and releases are queued up - this function reads the
        next press from the queue, and returns 1.  If no presses are queued, it
        returns 0.

        For example, if the button was pressed 2 times, and this function was
        called 3 times, the result would be:
            >>> print(button.one_press())
            1
            >>> print(button.one_press())
            1
            >>> print(button.one_press())
            0

        Alternatively, if `press` is `False`, this function returns releases
        instead of presses.
        """
        return self._one_edge(0 if press else 1)

    def wait(self, press=True, timeout=None):
        """Wait until a press occurs.

        This function blocks until a press occurs and (by default) returns
        `True`.  Because button presses and releases are queued up, it will
        return immediately if a press is already available before the function
        was called.

        If `timeout=None` (the default), the function will block forever until
        a press occurs.  If the `timeout` is a number 0 or greater, the
        function will block for up to `timeout` time in seconds (floats
        allowed).  If the `timeout` time expires before the button is pressed,
        the function returns `False`.

        Alternatively, if `press` is `False`, this function waits for releases
        instead of presses.
        """
        return self._wait(0 if press else 1, timeout=timeout)

    @classmethod
    def wait_many(cls, buttons, press=True, timeout=None):
        """Calls `rstem.button.Button.wait` on a list of buttons.

        Given a list of `buttons` this function will wait for any of them to be
        pressed, and return the index into the `buttons` list of the button
        that was pressed.  The `press` and `timeout` arguments are the same as
        for the `rstem.button.Button.wait` function.
        """
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
