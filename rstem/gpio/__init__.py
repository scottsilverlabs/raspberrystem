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

PINS = [2, 3, 4, 14, 15, 17, 18, 22, 23, 24, 25, 27]

active_pins = {}

class Pin(object):
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

class DisablePin(Pin):
    def _deactivate(self):
        with open(self.gpio_dir + "/direction", "w") as fdirection:
            fdirection.write("in")
        super()._deactivate()

__all__ = ['Output', 'DisablePin']

