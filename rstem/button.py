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
"""
This module provides interfaces to the buttons in the I/O RaspberrySTEM Cell.
"""

from threading import Thread, Event
from queue import Queue, Empty
import time
from rstem.gpio import Pin

class Button(Pin):
    """A button from a GPIO port.

    A `rstem.button.Button` configures a physical button hooked up to a GPIO
    pin.  The physical button, when pressed, should connect the GPIO pin to
    ground.

    `rstem.button.Button` provides a set of functions that make it easy to
    check if and when a button is pressed.  The `rstem.button.Button` object
    reads button presses in the background so that the calling program won't
    lose presses.  Presses and releases are kept in a queue that the caller can
    read at any time.

    More details: The GPIO is configured with an internal pullup so that when
    the button is NOT pressed, the GPIO input is high, and when the button is
    pressed, the input is low (shorted to ground).  Additionaly, The
    `rstem.button.Button` object handles button debouncing.
    """

    A = 4
    """GPIO number of the 'A' button on the GAMER keypad."""
    B = 17
    """GPIO number of the 'B' button on the GAMER keypad."""
    UP = 25
    """GPIO number of the 'UP' button on the GAMER keypad."""
    DOWN = 24
    """GPIO number of the 'DOWN' button on the GAMER keypad."""
    LEFT = 23
    """GPIO number of the 'LEFT' button on the GAMER keypad."""
    RIGHT = 18
    """GPIO number of the 'RIGHT' button on the GAMER keypad."""
    START = 27
    """GPIO number of the 'START' button on the GAMER keypad."""
    SELECT = 22
    """GPIO number of the 'SELECT' button on the GAMER keypad."""

    def __init__(self, pin):
        """Create a new `rstem.button.Button`.

        `pin` is the number of the GPIO as labeled on the RaspberrySTEM Lid
        Connector Board.  It is the same as the GPIO number used by the
        Broadcom processor on the Raspberry Pi.
        """

        super().__init__(pin)

        self._set_dir(output=False)

        self._enable_pullup(self.pin)

        self._fvalue = open(self.gpio_dir + "/value", "r")

        self._set_current()

        self._button_queue = Queue()
        self._poll_thread_stop = Event()
        self._poll_thread = Thread(target=self.__button_poll_thread, args=())
        self._poll_thread.daemon = True
        self._poll_thread.start()

    def _set_current(self):
        self._fvalue.seek(0)
        read = self._fvalue.read().strip()
        self.current = 1 if read == '1' else 0

    def __button_poll_thread(self):
        previous = -1

        bounce_time = 0.030
        while not self._poll_thread_stop.wait(bounce_time):
            self._set_current()
            if previous >= 0 and self.current != previous:
                self._button_queue.put(self.current)
            previous = self.current

    def _changes(self):
        releases, presses, level = 0, 0, self.current
        try:
            while True:
                level = self._button_queue.get_nowait()
                if level:
                    releases += 1
                else:
                    presses += 1
        except Empty:
            pass
        return releases, presses, level

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

    def _deactivate(self):
        if self._poll_thread:
            self._poll_thread_stop.set()
            self._poll_thread.join()
        super()._deactivate()

    def is_pressed(self, press=True):
        """Reports if the button is pressed.

        Returns `True` if the button is pressed, otherwise `False`.
        """
        releases, presses, level = self._changes()
        return not level

    def is_released(self):
        """Reports if the button is released.

        Equivalent to `not`&nbsp;`rstem.button.Button.is_pressed``()`.
        """
        return not self.is_pressed()

    def presses(self, press=True):
        """Returns the number of presses since presses/releases were last queried.

        Button presses and releases are queued up - this function reads all
        the presses/releases from the queue and returns the total number of
        presses.  Reading the full queue effectively resets the number of
        presses and releases to zero.

        Alternatively, if `press` is `False`, this function returns the number
        of releases since presses/releases were last queried.
        """
        releases, presses, level = self._changes()
        return presses if press else releases

    def releases(self):
        """Returns the number of releases since presses/releases were last queried.

        Equivalent to `rstem.button.Button.presses``(press=False)`.
        """
        return self.presses(press=False)

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

    # NOTE: Fake instancemethod as pdoc workaround.  See NOTE in docstring.
    def staticmethod_wait_many(buttons, press=True, timeout=None):
        """Calls `rstem.button.Button.wait` on a list of buttons.

        Given a list of `buttons` this function will wait for any of them to be
        pressed, and return the index into the `buttons` list of the button
        that was pressed.  The `press` and `timeout` arguments are the same as
        for the `rstem.button.Button.wait` function.

        **NOTE**: This is a `staticmethod` not an `instancemethod`, and the
        actual name does not include the prefix `staticmethod_`.  It is only
        shown with that prefix to allow it to be documented here.

        """
        # Python does not provide a way to wait on multiple Queues.  Big bummer.
        # To avoid overcomplicating this, we'll simply poll the queues.
        start = time.time()
        while timeout == None or timeout - (time.time() - start) > 0:
            for i, button in enumerate(buttons):
                button_found = button.wait(press=press, timeout=0)
                if button_found:
                    return i
            time.sleep(0.01)
        return None

    @staticmethod
    def wait_many(*args, **kwargs):
        return Button.staticmethod_wait_many(*args, **kwargs)

    """ TBD:
    def callback(self): callback if press, release, or either
    """

__all__ = ['Button']
