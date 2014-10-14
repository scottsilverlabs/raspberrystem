import os
import sys
import select
import time
from threading import Thread, Lock
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


class Port:
    def __init__(self, pin):
        self.gpio_dir = "/sys/class/gpio/gpio%d" % pin
        self.pin = pin
        self.direction = DISABLED
        self.edge = NONE
        self.last = 1
        self.mutex = Lock()
        self.poll_thread = None
        self.poll_thread_running = False
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
        print("Self " + str(self.gpio_dir))
        f = open(self.gpio_dir + "/value", "r")
        po = select.epoll()
        po.register(f, select.POLLIN | select.EPOLLPRI | select.EPOLLET)
        last_time = 0
        first_time = True  # used to ignore first trigger

        while(self.poll_thread_running):
            print(po.poll())   # TODO: implement timeout?
            f.seek(0)
            print("Running callback...")
            if not first_time:
                timenow = time.time()
                if timenow - last_time > bouncetime*1000 or last_time == 0:
                    callback(self.pin)
                    last_time = timenow
            else:
                first_time = False
            # time.sleep(bouncetime/1000)
            print("Bouncing back...")
        f.close()

    def __set_edge(self, edge):
        with self.mutex:
            with open(self.gpio_dir + "/edge", "w") as fedge:
                self.edge = edge
                fedge.write(edge)

    def remove_edge_detect(self):
        """Removes edge detect interrupt"""
        self.edge_detect(NONE)
        self.poll_thread_running = False
        self.poll_thread.join(1)
        if self.poll_thread.isAlive():
            raise RuntimeError("Poll thread didn't die!")

    def wait_for_edge(self, edge):
        """Blocks until the given edge has happened
        @param edge: Either gpio.FALLING, gpio.RISING, gpio.BOTH
        @param edge: string
        @throws: ValueError
        """
        if edge not in [RISING, FALLING, BOTH]:
            raise ValueError("Invalid edge!")
        self.__set_edge(edge)

        # wait for edge
        f = open(self.gpio_dir + "/value", "r")
        po = select.epoll()
        po.register(f, select.POLLIN | select.EPOLLPRI | select.EPOLLET)
        # last_time = 0
        first_time = True  # used to ignore first trigger

        while True:
            print(po.poll())   # TODO: implement timeout?
            f.seek(0)
            print("Running callback...")
            if not first_time:
                callback(self.pin)
                break
            else:
                first_time = False
        f.close()

    def edge_detect(self, edge, callback=None, bouncetime=200):
        """Sets up edge detection interrupt.
        @param edge: either gpio.NONE, gpio.RISING, gpio.FALLING, or gpio.BOTH
        @type edge: int
        @param callback: Function to call when given edge has been detected.
        @type callback: function
        @note: First parameter of callback function will be the port number of gpio that called it.
        """
        if callback is None and edge != NONE:
            raise ValueError("Callback function must be given if edge is not NONE")
        if edge not in [NONE, RISING, FALLING, BOTH]:
            raise ValueError("Edge must be NONE, RISING, FALLING, or BOTH")

        self.__set_edge(edge)

        if edge != NONE:
            self.poll_thread_running = True
            self.poll_thread = Thread(target=Port.__poll_thread_run, args=(self, callback, bouncetime))
            self.poll_thread.start()
        else:
            self.poll_thread_running = False  # TODO: ????

    def configure(self, direction):
        """Configure the GPIO port to either be an input, output or disabled.
        @param direction: Either gpio.INPUT, gpio.OUTPUT, or gpio.DISABLED
        @type direction: int
        """
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
        # TODO: make work for any type of edge change and rename function
        """Detects whether the GPIO has been clicked or on since the port has been initialized or
        since the last time was_clicked() has been called.
        @returns: boolean
        """
        level = self.get_level()
        clicked = level == 1 and self.last == 0
        self.last = level
        return clicked

    def get_level(self):
        """Returns the current level of the GPIO port.
        @returns: int (1 for HIGH, 0 for LOW)
        @note: The GPIO ports are active low.
        """
        with self.mutex:
            self.fvalue.seek(0)
            return int(self.fvalue.read())

    def set_level(self, level):
        """Currently not implemented.
        @throws: NotImplementedError
        """
        with self.mutex:
            raise NotImplementedError()


class Ports:
    def __init__(self):
        self.gpios = [Port(i) for i in range(max(PINS) + 1)]

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
g = Ports()
for name in ['configure', 'get_level', 'set_level', 'was_clicked']:
    globals()[name] = getattr(g, name)
