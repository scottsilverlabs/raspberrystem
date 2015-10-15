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
'''
This module provides interfaces to GPIOs - useful for the lighting LEDs in the I/O RaspberrySTEM
Cell, and other RaspberrySTEM Cells.
'''

import os
import time
from functools import partial
import re

PINS = range(2, 28)

PULLUP_CMD = '/usr/local/bin/pullup.sbin'
GPIO_EXPORT_FILE = '/sys/class/gpio/export'
GPIO_UNEXPORT_FILE = '/sys/class/gpio/unexport'
GPIO_PIN_FORMAT_STRING = '/sys/class/gpio/gpio%d'

PULL_DISABLE = 0
PULL_DOWN = 1
PULL_UP = 2

def _global_pin_init():
    # Disable all GPIOs to start.  Note that unexporting a GPIO if it hasn't
    # been exported will fail - but we will ignore it.
    for pin in PINS:
        try:
            with open(GPIO_UNEXPORT_FILE, 'w') as f:
                f.write('%d' % pin)
        except IOError:
            pass

def retry_func_on_error(func, tries=10, sleep=0.01, exc=IOError):
    for i in range(tries):
        try:
            ret = func()
        except exc as err:
            time.sleep(sleep)
            sleep *= 2
        else:
            break
    else:
        raise err
    return ret

class Pin(object):
    _global_pin_init()

    def __init__(self, pin):
        self._board_rev = self.board_rev()
        self.gpio_dir = GPIO_PIN_FORMAT_STRING % pin
        self.pin = pin
        if pin in PINS:
            if os.path.exists(self.gpio_dir):
                raise IOError('GPIO pin already in use')

            with open(GPIO_EXPORT_FILE, 'w') as f:
                f.write('%d\n' % pin)

            # Repeat trying to configure GPIO as input (default).  Repeats
            # required because this can fail when run right after the pin
            # is exported in /sys.  Once it passes, we know the pin is
            # ready to use.
            retry_func_on_error(partial(self._set_output, False))
        else:
            raise ValueError('Invalid GPIO pin')
        self._write_gpio_file('direction', 'in')
        self._write_gpio_file('active_low', '0')
        self._write_gpio_file('edge', 'none')
        self._set_pull(PULL_DISABLE)

    @staticmethod
    def board_rev():
        with open('/proc/cpuinfo') as f:
            cpuinfo = f.read()
        matches = re.findall(
            '^Revision.*([0-9A-F]{4})$',
            cpuinfo,
            flags=(re.MULTILINE|re.IGNORECASE)
            )
        board_rev = int(matches[0], 16)
        return board_rev

    def _write_gpio_file(self, filename, value):
        def write_val(filename, value):
            with open(self.gpio_dir + '/' + filename, 'w') as f:
                f.write(value)
        retry_func_on_error(partial(write_val, filename, value))

    def _set_output(self, output, starts_off=True):
        if output:
            is_low = self._active_low and not starts_off or not self._active_low and starts_off
            direction = 'low' if is_low else 'high'
        else:
            direction = 'in'
        self._write_gpio_file('direction', direction)

    def _set_pull(self, pull):
        if not pull in [PULL_UP, PULL_DOWN, PULL_DISABLE]:
            raise ValueError('Invalid pull type')
        os.system('%s %d %d %d' % (PULLUP_CMD, self.pin, pull, self._board_rev))

    def disable(self):
        '''Disable the GPIO pin.'''
        with open(GPIO_UNEXPORT_FILE, 'w') as f:
            f.write('%d\n' % self.pin)


class Output(Pin):
    '''A GPIO output.

    An `rstem.gpio.Output` configures a GPIO pin as an output.  The pin can then used as a
    programmable switch to drive LEDs, motor drivers, relays and other devices.
    '''
    def __init__(self, pin, active_low=True):
        '''Create a new `Output`.

        `pin` is the number of the GPIO as labeled on the RaspberrySTEM Lid
        connector.  It is the GPIO number used by the Broadcom processor on
        the Raspberry Pi.

        If `active_low=True` (the default), then the output will be set LOW
        (grounded, i.e. 0 volts) when the output is turned `on`.  If
        `active_low=False`, then the output will be set HIGH (the supply
        voltage, i.e. 3.3 volts) when the output is turned `on`.
        '''
        super().__init__(pin)
        self._active_low = active_low
        self._set_output(True)
        self._fvalue = retry_func_on_error(partial(open, self.gpio_dir + '/value', 'w'))

    def _set(self, level):
        self._fvalue.seek(0)
        self._fvalue.write('1' if level else '0')
        self._fvalue.flush()

    def on(self):
        '''Turn the GPIO output on (repects `active_low` setting).'''
        self._set(not self._active_low)

    def off(self):
        '''Turn the GPIO output off (repects `active_low` setting).'''
        self._set(self._active_low)

    def disable(self):
        self._fvalue.close()
        super().disable()

class Input(Pin):
    '''A GPIO input.

    An `rstem.gpio.Input` configures a GPIO pin as an input.  The pin can then
    used as to read the logic level of the pin - useful for reading the state
    of switches, sensors, and other electronics.
    '''
    def __init__(self, pin, active_low=False, pull=PULL_DISABLE):
        '''Create a new `Input`.

        `pin` is the number of the GPIO as labeled on the RaspberrySTEM Lid
        connector.  It is the GPIO number used by the Broadcom processor on
        the Raspberry Pi.

        If `active_low=True` (the default), then when the input is externally
        set LOW (grounded, i.e. 0 volts), it is considered `on`.  If
        `active_low=False`, then when the input is externally set HIGH (the
        supply voltage, i.e. 3.3 volts), it is considered `on`.

        `pull` is the state of the GPIO internal pullup/down.
        If `pull` is `PULL_DISABLE`, then the internal pullup is diabled.
        If `pull` is `PULL_UP`, then the internal pullup is enabled.
        If `pull` is `PULL_DOWN`, then the internal pulldown is enabled.
        '''
        super().__init__(pin)
        self._active_low = active_low
        self._set_output(False)
        self._set_pull(pull)
        self._fvalue = retry_func_on_error(partial(open, self.gpio_dir + '/value', 'r'))

    def configure(self, pull=None):
        self._set_pull(pull)

    def _get(self):
        self._fvalue.seek(0)
        return 1 if self._fvalue.read().strip() == '1' else 0

    def is_on(self):
        '''Return the GPIO input state (repects `active_low` setting).'''
        return bool(not self._get() if self._active_low else self._get())

    def is_off(self):
        '''Return the GPIO input state (repects `active_low` setting).'''
        return not self.is_on()

    def disable(self):
        self._fvalue.close()
        super().disable()

__all__ = ['Output', 'Input', PULL_DISABLE, PULL_UP, PULL_DOWN]

