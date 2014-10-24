import os
import sys
import select
import time
from threading import Thread, Lock, Event
import types

PINS = [2, 3, 4, 14, 15, 17, 18, 22, 23, 24, 25, 27]

# Directions
OUTPUT = 1
INPUT = 2
DISABLED = 3

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


class Pin:
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
        here = os.path.dirname(os.path.realpath(__file__))
        os.system(here + "/pullup.sbin %d %d" % (pin, enable))

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

    def remove_edge_detect(self):
        """Removes edge detect interrupt"""
        self.edge_detect(NONE)
        if self.poll_thread and self.poll_thread.isAlive():
            # self.poll_thread_running = False
            self.poll_thread_stop.set()

            while self.poll_thread.isAlive():
                self.poll_thread.join(1)


    def wait_for_edge(self, edge):
        """Blocks until the given edge has happened
        @param edge: Either gpio.FALLING, gpio.RISING, gpio.BOTH
        @param edge: string
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

    def edge_detect(self, edge, callback=None, bouncetime=200):
        """Sets up edge detection interrupt.
        @param edge: either gpio.NONE, gpio.RISING, gpio.FALLING, or gpio.BOTH
        @type edge: int
        @param callback: Function to call when given edge has been detected.
        @type callback: function
        @note: First parameter of callback function will be the pint number of gpio that called it.
        """
        if self.direction != INPUT:
            raise ValueError("GPIO must be configured to be an input first.")
        if callback is None and edge != NONE:
            raise ValueError("Callback function must be given if edge is not NONE")
        if edge not in [NONE, RISING, FALLING, BOTH]:
            raise ValueError("Edge must be NONE, RISING, FALLING, or BOTH")

        self.__set_edge(edge)

        if edge != NONE:
            self.poll_thread_stop = Event()
            self.poll_thread = Thread(target=Pin.__poll_thread_run, args=(self, callback, bouncetime))
            self.poll_thread.start()


    def configure(self, direction):
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
                elif direction == INPUT:
                    self.__enable_pullup(self.pin)
                    fdirection.write("in")
                    self.fvalue = open(self.gpio_dir + "/value", "r")
                elif direction == DISABLED:
                    fdirection.write("in")
                    self.fvalue.close()

    def was_clicked(self):
        # TODO: make work for any type of edge change and rename function
        """Detects whether the GPIO has been clicked or on since the pin has been initialized or
        since the last time was_clicked() has been called.
        @returns: boolean
        """
        level = self.get_level()
        clicked = level == 1 and self.last == 0
        self.last = level
        return clicked

    def get_level(self):
        """Returns the current level of the GPIO pin.
        @returns: int (1 for HIGH, 0 for LOW)
        @note: The GPIO pins are active low.
        """
        if self.direction != INPUT:
            raise ValueError("GPIO must be configured to be an INPUT!")
        with self.mutex:
            self.fvalue.seek(0)
            return int(self.fvalue.read())

    def set_level(self, level):
        """Sets the level of the GPIO port.
        @param level: Level to set. Must be either HIGH or LOW.
        @param level: int
        """
        if self.direction != OUTPUT:
            raise ValueError("GPIO must be configured to be an OUTPUT!")
        if level != 0 and level != 1:
            raise ValueError("Level must be either 1 or 0.")
        with self.mutex:
            # write value wasn't working for some reason...
            os.system("echo %s > %s/value" % (str(level), self.gpio_dir))
            # self.fvalue.seek(0)
            # self.fvalue.write(str(level))


class Pins:
    def __init__(self):
        self.gpios = [Pin(i) for i in range(max(PINS) + 1)]

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
g = Pins()
for name in ['configure', 'get_level', 'set_level', 'was_clicked']:
    globals()[name] = getattr(g, name)
