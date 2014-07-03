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
import sys
import time
from threading import Thread, Lock
from collections import namedtuple
import types

PINS=[2,3,4,14,15,17,18,22,23,24,25,27]
OUTPUT=1
INPUT=2
DISABLED=3

ARG_PULL_DISABLE=0
ARG_PULL_DOWN=1
ARG_PULL_UP=2

class Gpio:
    def __init__(self, pin):
        self.gpio_dir = "/sys/class/gpio/gpio%d" % pin
        self.pin = pin
        self.direction = DISABLED
        self.last = 1
        self.mutex = Lock()
        if pin in PINS:
            if not os.path.exists(self.gpio_dir):
                with open("/sys/class/gpio/export", "w") as f:
                    f.write("%d\n" % pin)

    def __pullup(self, pin, enable):
        here = os.path.dirname(os.path.realpath(__file__))
        os.system(here + "/pullup.sbin %d %d" % (pin, enable))

    def __enable_pullup(self, pin):     self.__pullup(pin, ARG_PULL_UP)
    def __disable_pullup(self, pin):    self.__pullup(pin, ARG_PULL_DISABLE)
    def __enable_pulldown(self, pin):   self.__pullup(pin, ARG_PULL_DOWN)
    def __disable_pulldown(self, pin):  self.__pullup(pin, ARG_PULL_DISABLE)

    def configure(self, direction):
        if direction == OUTPUT:
            raise NotImplementedError()
        elif direction == INPUT:
            pass
        elif direction == DISABLED:
            pass
        else:
            raise ValueError("Direction must be INPUT, OUTPUT or DISABLED")

        with self.mutex:
            with open(self.gpio_dir + "/direction", "w") as fdirection:
                self.direction = direction
                if direction == OUTPUT:
                    # For future use
                    fdirection.write("out")
                    self.fvalue = open(self.gpio_dir + "/value", "w")
                elif direction == INPUT:
                    self.__enable_pullup(self.pin)
                    fdirection.write("in")
                    self.fvalue = open(self.gpio_dir + "/value", "r")
                elif direction == DISABLED:
                    fdirection.write("in")
                    self.fvalue.close()

    def was_clicked(self):
        level = self.get_level()
        clicked = level == 1 and self.last == 0
        self.last = level
        return clicked

    def get_level(self):
        with self.mutex:
            self.fvalue.seek(0)
            return int(self.fvalue.read())

    def set_level(self, level):
        with self.mutex:
            raise NotImplementedError()


class Gpios:
    def __init__(self):
        self.gpios = [Gpio(i) for i in range(max(PINS) + 1)]

    def __validate_gpio(self, pin, direction):
        class UninitializedError(Exception):
            pass
        if not pin in PINS:
            raise ValueError("Invalid GPIO")
        if self.gpios[pin].direction != direction:
            raise UninitializedError()

    def configure(self, pin, direction):
        if not pin in PINS:
            raise ValueError("Invalid GPIO")
        self.gpios[pin].configure(direction)
                
    def was_clicked(self):
        inputs = [g for g in self.gpios if g.direction == INPUT]
        return [g.pin for g in inputs if g.was_clicked()]

    def get_level(self, pin):
        self.__validate_gpio(pin, INPUT)
        return self.gpios[pin].get_level()

    def set_level(self, pin, level):
        self.__validate_gpio(pin, OUTPUT)
        self.gpios[pin].set_level(level)

# Export functions in this module
g = Gpios()
for name in ['configure', 'get_level', 'set_level', 'was_clicked']:
    globals()[name] = getattr(g, name)

def _main():
    configure(2, INPUT)
    while True:
        c = was_clicked()
        if c:
            print(c)
        time.sleep(0.030)

if __name__ == "__main__":
    _main()

