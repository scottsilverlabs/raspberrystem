import testing_log
import importlib
import testing
import pytest
import rstem.gpio as g
import time
from functools import wraps

'''
Automatic tests of gpio module via loopback output to input

Short GPIO 23 to 24.
'''

OUTPUT_PIN = 23
INPUT_PIN = 24

def io_setup(func):
    @wraps(func)
    def wrapper():
        # Setup
        i = g.Input(INPUT_PIN)
        o = g.Output(OUTPUT_PIN)

        passed = func(i, o)

        # Teardown
        g.Input(OUTPUT_PIN)
        return passed
    return wrapper

@testing.automatic
@io_setup
def output_starts_off(i, o):
    return i.is_off()

@testing.automatic
@io_setup
def output_turned_on(i, o):
    o.off()
    o.on()
    return i.is_on()

@testing.automatic
@io_setup
def output_turned_off(i, o):
    o.on()
    o.off()
    return i.is_off()

@testing.automatic
@io_setup
def output_turned_on_via_set(i, o):
    o.off()
    o.level = 1
    return i.is_on()

@testing.automatic
@io_setup
def output_turned_off_via_set(i, o):
    o.on()
    o.level = 0
    return i.is_off()

@testing.automatic
@io_setup
def io_on_off_sequence(i, o):
    on_times = 0
    off_times = 0
    TRIES = 1000
    for i in range(TRIES):
        o.on()
        if i.is_on:
            on_times += 1
        o.off()
        if i.is_off:
            off_times += 1
    passed = on_times == TRIES and off_times == TRIES
    if not passed:
        print("Failed: on_times {}, off_times {}, TRIES {}".format(on_times, off_times, TRIES))
    return passed

@testing.automatic
@io_setup
def output_init_start_off_false(i, o):
    return False

@testing.automatic
@io_setup
def output_init_active_low_false(i, o):
    return False

@testing.automatic
@io_setup
def input_is_off(i, o):
    o.off()
    return i.is_off()

@testing.automatic
@io_setup
def input_is_on(i, o):
    o.off()
    return i.is_off()

@testing.automatic
@io_setup
def input_is_off_via_get(i, o):
    o.on()
    return i.level

@testing.automatic
@io_setup
def input_is_on_via_get(i, o):
    o.off()
    return not i.level

@testing.automatic
@io_setup
def input_is_on_via_get_triplet(i, o):
    # TBD
    # Add optional parameter to get() triplet of falling, rising, and current
    # values
    # 
    return False

@testing.automatic
@io_setup
def input_wait_for_change(i, o):
    return False

@testing.automatic
@io_setup
def input_wait_for_change_with_timeout(i, o):
    return False

@testing.automatic
@io_setup
def input_call_if_changed(i, o):
    return False

@testing.automatic
@io_setup
def input_call_if_changed_disable(i, o):
    return False

@testing.automatic
@io_setup
def input_init_active_low_false(i, o):
    return False

@testing.automatic
@io_setup
def input_init_poll_period_slow(i, o):
    return False

@testing.automatic
@io_setup
def input_init_pullup(i, o):
    return False

@testing.automatic
@io_setup
def input_init_pulldown(i, o):
    return False

@testing.automatic
@io_setup
def input_init_pullnone(i, o):
    return False

@testing.automatic
@io_setup
def input_button_is_pressed(i, o):
    o.off()
    return i.is_pressed()

@testing.automatic
@io_setup
def input_button_is_released(i, o):
    o.off()
    return i.is_released()

