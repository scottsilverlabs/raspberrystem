import os
import sys
import time
from threading import Thread, Lock
from collections import namedtuple
import types

GPIOS=[2,3,4,14,15,17,18,22,23,24,25,27]
POLL_RATE=0.010
OUTPUT=1
INPUT=2
DISABLED=3

class Gpio:
    def __init__(self, gpio):
        self.gpio_dir = "/sys/class/gpio/gpio%d" % gpio
        self.gpio = gpio
        self.direction = DISABLED
        if gpio in GPIOS:
            if not os.path.exists(self.gpio_dir):
                with open("/sys/class/gpio/export", "w") as f:
                    f.write("%d\n" % gpio)

    def configure(self, direction):
        if direction == OUTPUT:
            raise NotImplementedError()
        elif direction == INPUT:
            pass
        elif direction == DISABLED:
            pass
        else:
            raise ValueError("Direction must be INPUT, OUTPUT or DISABLED")

        with open(self.gpio_dir + "/direction", "w") as fdirection:
            self.direction = direction
            if direction == OUTPUT:
                # For future use
                fdirection.write("out")
                self.fvalue = open(self.gpio_dir + "/value", "w")
            elif direction == INPUT:
                fdirection.write("in")
                self.fvalue = open(self.gpio_dir + "/value", "r")
            elif direction == DISABLED:
                fdirection.write("in")
                self.fvalue.close()

    def get_level(self):
        self.fvalue.seek(0)
        return int(self.fvalue.read())

    def set_level(self, level):
        raise NotImplementedError()


class Gpios:
    def __init__(self):
        self.gpios = [Gpio(i) for i in range(max(GPIOS) + 1)]
        self.mutex = Lock()
        t = Thread(target=self.__gpio_polling_thread)
        t.daemon = True
        t.start()

    def __validate_gpio(self, gpio, direction):
        class UninitializedError(Exception):
            pass
        if not gpio in GPIOS:
            raise ValueError("Invalid GPIO")
        if self.gpios[gpio].direction != direction:
            raise UninitializedError()

    def __gpio_polling_thread(self):
        while True:
            with self.mutex:
                pass
            time.sleep(POLL_RATE)

    def configure(self, gpio, direction):
        print self, gpio, direction
        if not gpio in GPIOS:
            raise ValueError("Invalid GPIO")
        with self.mutex:
            self.gpios[gpio].configure(direction)
                
    def get_presses(self, gpio):
        self.__validate_gpio(gpio, INPUT)
        raise NotImplementedError()

    def get_level(self, gpio):
        self.__validate_gpio(gpio, INPUT)
        return self.gpios[gpio].get_level()

    def set_level(self, gpio, level):
        self.__validate_gpio(gpio, OUTPUT)
        self.gpios[gpio].set_level(level)

# Export functions in this module
g = Gpios()
for name in ['configure', 'get_presses', 'get_level', 'set_level']:
    globals()[name] = getattr(g, name)

def _main():
    configure(2, INPUT)
    for i in range(20):
        print get_level(2)
        time.sleep(0.5)

if __name__ == "__main__":
    _main()

