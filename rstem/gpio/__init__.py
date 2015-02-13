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
This module provides interfaces to GPIOs - useful for the lighting LEDs in the LED RaspberrySTEM
Cell, and other RaspberrySTEM Cells.
'''

import os
import time

PINS = [2, 3, 4, 14, 15, 17, 18, 22, 23, 24, 25, 27]

active_pins = {}

class Pin(object):
    _ARG_PULL_DISABLE = 0
    _ARG_PULL_DOWN = 1
    _ARG_PULL_UP = 2

    def __init__(self, pin):
        self.gpio_dir = '/sys/class/gpio/gpio%d' % pin
        self.pin = pin
        if pin in PINS:
            if not os.path.exists(self.gpio_dir):
                with open('/sys/class/gpio/export', 'w') as f:
                    f.write('%d\n' % pin)

                # Repeat trying to configure GPIO as input (default).  Repeats
                # required because this can fail when run right after the pin
                # is exported in /sys.  Once it passes, we know the pin is
                # ready to use.
                TRIES = 12
                SLEEP = 0.01
                while TRIES:
                    try:
                        self._set_dir(output=False)
                    except IOError:
                        # Reraise the error if that was our last try
                        if TRIES == 1:
                            raise
                        time.sleep(SLEEP)
                    else:
                        break
                    TRIES -= 1
                    SLEEP *= 2
        else:
            raise ValueError('Invalid GPIO pin')

        global active_pins
        if pin in active_pins:
            active_pins[pin]._deactivate()
        active_pins[pin] = self

    def _write_gpio_file(self, filename, value):
        with open(self.gpio_dir + '/' + filename, 'w') as f:
            f.write(value)

    def _set_dir(self, output=False, starts_off=True):
        if output:
            is_low = self._active_low and not starts_off or not self._active_low and starts_off
            direction = 'low' if is_low else 'high'
        else:
            direction = 'in'
        self._write_gpio_file('direction', direction)

    def _set_active_low(self, enabled=True):
        self._write_gpio_file('active_low', '1' if enabled else '0')

    def _pullup(self, pin, enable):
        os.system('pullup.sbin %d %d' % (pin, enable))

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
        self._set_dir(output=True)
        self._fvalue = open(self.gpio_dir + '/value', 'w')

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

class DisablePin(Pin):
    '''Disable a previously used GPIO pin.'''

    def __init__(self, *args, **kwargs):
        '''Disable a previously used GPIO pin.

        `pin` is the number of the GPIO as labeled on the RaspberrySTEM Lid
        connector.  It is the GPIO number used by the Broadcom processor on
        the Raspberry Pi.
        '''
        super().__init__(*args, **kwargs)

    def _deactivate(self):
        self._set_dir(output=False)
        super()._deactivate()

__all__ = ['Output', 'DisablePin']

